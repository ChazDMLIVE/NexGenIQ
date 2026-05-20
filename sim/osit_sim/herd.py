"""
The whole-herd stochastic simulation core of osit-sim.

Simulates a beef cow-calf enterprise animal by animal and year by year,
following NexGenIQ Phase 3 Part 3B Section 2.5.1: initialise a cow herd,
burn in so the age structure stabilises, then for each planning-horizon
year run the annual cycle (mate, conceive, calve, grow calves to the sale
endpoint, account for economics, cull and replace), accumulating
discounted net return.

The simulation is stochastic; reproducibility is guaranteed by seeding the
RNG (the basis for the common-random-numbers technique used by the MEV
engine, Phase 3 Part 3B Section 2.5.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .economics import endpoint_revenue, herd_costs
from .genetics import TraitGenetics, breed_effect, heterosis_value
from .inputs import (
    BreedComposition,
    EconomicScenario,
    ProductionSystem,
    SimulationControls,
)

_MAX_COW_AGE = 11
_FIRST_CALVING_AGE = 2

# Replacement-female economics. Developing a heifer from weaning to first
# calving (~2 years of feed, health and care) is a real cost; so is buying
# a bred replacement on the open market. These are what make stayability
# (fewer replacements needed) economically valuable.
_REPLACEMENT_DEVELOPMENT_COST = 900.0   # rear an own heifer to first calving
_PURCHASED_REPLACEMENT_COST = 1800.0    # buy a bred replacement female


@dataclass
class SimulationResult:
    """The outcome of a herd simulation.

    Attributes
    ----------
    net_present_profit:
        Discounted whole-herd net return over the planning horizon.
    mean_annual_profit:
        Undiscounted mean annual net return.
    calves_weaned_per_year:
        Average calves weaned per year.
    mean_cow_age:
        Mean cow age at the end of the run.
    converged:
        True if the cow age distribution is biologically sensible.
    """

    net_present_profit: float
    mean_annual_profit: float
    calves_weaned_per_year: float
    mean_cow_age: float
    converged: bool = True


@dataclass
class _Cow:
    """A single breeding cow within the simulation (internal)."""

    age: int
    genetics: dict[str, float] = field(default_factory=dict)
    heterozygosity: float = 0.0
    breeds: dict[str, float] = field(default_factory=dict)
    #: If this animal is a candidate replacement heifer, the value she
    #: would realise if sold as a weaned calf instead of being retained.
    sale_value: float = 0.0


def _sample_composition(comps, rng):
    """Randomly draw one breed-composition class by its fraction."""
    r = rng.random()
    cumulative = 0.0
    for comp in comps:
        cumulative += comp.fraction
        if r <= cumulative:
            return comp
    return comps[-1]


def _heterozygosity(breeds):
    """Breed heterozygosity = 1 - sum of squared breed fractions."""
    return 1.0 - sum(f * f for f in breeds.values())


def _draw_genetics(genetics, rng, shift=None):
    """Draw additive genetic values for one animal.

    Each trait's additive value is a normal draw, mean 0 (deviation from
    the base), SD the trait's genetic SD. `shift` adds a fixed amount to a
    trait's genetic mean - the perturbation hook the MEV engine uses.
    Traits with a maternal component also get a `<code>_M` maternal value.
    """
    shift = shift or {}
    values: dict[str, float] = {}
    for code, g in genetics.items():
        values[code] = rng.normal(0.0, g.genetic_sd) + shift.get(code, 0.0)
        if g.has_maternal:
            values[f"{code}_M"] = rng.normal(0.0, g.maternal_sd)
    return values


def _initial_age_distribution():
    """A reasonable starting cow age distribution (proportions, age 2..11)."""
    raw = [0.16, 0.15, 0.135, 0.12, 0.105, 0.09, 0.075, 0.06, 0.05, 0.04]
    total = sum(raw)
    return [r / total for r in raw]


def _build_initial_herd(system, genetics, rng, shift):
    """Create the founding cow herd."""
    dist = _initial_age_distribution()
    herd: list[_Cow] = []
    for _ in range(system.herd_size):
        age = _FIRST_CALVING_AGE + int(rng.choice(len(dist), p=dist))
        comp = _sample_composition(system.cow_breed_composition, rng)
        herd.append(
            _Cow(
                age=age,
                genetics=_draw_genetics(genetics, rng, shift),
                heterozygosity=_heterozygosity(comp.breeds),
                breeds=dict(comp.breeds),
            )
        )
    return herd


def _calf_trait(code, dam, sire_genetics, sire_breeds, genetics, rng):
    """Compute one observed trait value for a calf.

    Phenotype = base mean + breed component + direct additive value
    (half dam + half sire) + dam maternal contribution + heterosis +
    residual.
    """
    g = genetics[code]

    calf_breeds: dict[str, float] = {}
    for b, f in dam.breeds.items():
        calf_breeds[b] = calf_breeds.get(b, 0.0) + f / 2.0
    for b, f in sire_breeds.items():
        calf_breeds[b] = calf_breeds.get(b, 0.0) + f / 2.0
    calf_het = _heterozygosity(calf_breeds)

    breed_component = sum(
        frac * breed_effect(breed, code)
        for breed, frac in calf_breeds.items()
    )
    direct = 0.5 * dam.genetics.get(code, 0.0) + 0.5 * (
        sire_genetics.get(code, 0.0)
    )
    maternal = 0.0
    if g.has_maternal:
        maternal = dam.genetics.get(f"{code}_M", 0.0)
        if code == "WW":
            maternal += dam.genetics.get("MILK", 0.0)
    het = heterosis_value(code, calf_het)
    residual = rng.normal(0.0, g.residual_sd)
    return g.mean + breed_component + direct + maternal + het + residual


def run_simulation(
    system: ProductionSystem,
    economics: EconomicScenario,
    controls: SimulationControls,
    genetics: dict[str, TraitGenetics],
    *,
    seed: int | None = None,
    genetic_shift: dict[str, float] | None = None,
) -> SimulationResult:
    """Simulate the cow-calf enterprise and return its profitability.

    Parameters
    ----------
    system, economics, controls, genetics:
        The simulation inputs.
    seed:
        RNG seed for this single herd. The same seed for a baseline and a
        perturbed run is the common-random-numbers technique.
    genetic_shift:
        Optional fixed shift applied to one or more traits' genetic means.

    Returns
    -------
    SimulationResult
        Discounted net-present profit and herd summary statistics.
    """
    rng = np.random.default_rng(
        controls.seed if seed is None else seed
    )
    herd = _build_initial_herd(system, genetics, rng, genetic_shift)

    burn_in = controls.burn_in_years if system.heifer_retention else 0
    annual_profits: list[float] = []
    annual_weaned: list[float] = []
    discounted_total = 0.0

    total_years = burn_in + controls.planning_horizon_years
    for year in range(total_years):
        measured = year >= burn_in
        year_profit, weaned, herd = _simulate_year(
            herd, system, economics, genetics, rng, genetic_shift
        )
        if measured:
            measured_year = year - burn_in
            discount = 1.0 / (
                (1.0 + economics.discount_rate) ** measured_year
            )
            discounted_total += year_profit * discount
            annual_profits.append(year_profit)
            annual_weaned.append(weaned)

    mean_age = float(np.mean([c.age for c in herd])) if herd else 0.0
    return SimulationResult(
        net_present_profit=discounted_total,
        mean_annual_profit=(
            float(np.mean(annual_profits)) if annual_profits else 0.0
        ),
        calves_weaned_per_year=(
            float(np.mean(annual_weaned)) if annual_weaned else 0.0
        ),
        mean_cow_age=mean_age,
        converged=_FIRST_CALVING_AGE <= mean_age <= _MAX_COW_AGE,
    )


def _simulate_year(herd, system, economics, genetics, rng, shift):
    """Simulate one production year.

    Returns (net_profit, calves_weaned, next_year_herd).

    Replacement economics (Phase 3 Part 3B Section 2.5.1): cows are culled
    on age and on genetic stayability; each opening is then filled by a
    reared replacement heifer, and each replacement carries a development
    cost (the feed and care to raise her to first calving). Better
    stayability therefore means fewer culls, fewer reared replacements,
    and lower total development cost - which is what gives STAY a
    positive economic value.
    """
    sire_comp = _sample_composition(system.bull_breed_composition, rng)
    sire_genetics = _draw_genetics(genetics, rng, shift)

    revenue = 0.0
    calves_weaned = 0
    heifer_pool: list[_Cow] = []

    for cow in herd:
        # Conception, modulated by the cow's heifer-pregnancy genetics so
        # HP carries a real economic value.
        hp_adj = cow.genetics.get("HP", 0.0) / 100.0
        conception_p = min(0.999, max(0.0,
                                      system.conception_rate + hp_adj))
        if rng.random() > conception_p:
            continue

        # Calving loss, modulated by calving-ease direct (CED).
        ced_adj = cow.genetics.get("CED", 0.0) / 100.0
        loss_p = min(0.999, max(0.0, system.calving_loss_rate - ced_adj))
        if rng.random() < loss_p:
            continue

        calves_weaned += 1
        calf_sex = "S" if rng.random() < 0.5 else "F"

        traits = {
            code: _calf_trait(
                code, cow, sire_genetics, sire_comp.breeds, genetics, rng
            )
            for code in genetics
        }

        if system.heifer_retention and calf_sex == "F":
            # A heifer calf is a *potential* replacement: held back from
            # the sale and added to the pool. Whether she is actually
            # kept (and developed at a cost) depends on how many openings
            # the cull step creates - decided below.
            heifer_genetics: dict[str, float] = {}
            for code in genetics:
                base = 0.5 * cow.genetics.get(code, 0.0) + 0.5 * (
                    sire_genetics.get(code, 0.0)
                )
                ms = rng.normal(0.0, genetics[code].genetic_sd / 2.0)
                heifer_genetics[code] = base + ms
                if genetics[code].has_maternal:
                    heifer_genetics[f"{code}_M"] = rng.normal(
                        0.0, genetics[code].maternal_sd
                    )
            calf_breeds: dict[str, float] = {}
            for b, f in cow.breeds.items():
                calf_breeds[b] = calf_breeds.get(b, 0.0) + f / 2
            for b, f in sire_comp.breeds.items():
                calf_breeds[b] = calf_breeds.get(b, 0.0) + f / 2
            heifer_pool.append(
                _Cow(
                    age=_FIRST_CALVING_AGE - 1,
                    genetics=heifer_genetics,
                    heterozygosity=_heterozygosity(calf_breeds),
                    breeds=calf_breeds,
                )
            )
            # Her weaning-weight value is still realised as a weaned-calf
            # sale value if she is NOT kept; accounted for after culling.
        else:
            # Steer (or a heifer in a terminal herd): sold at the endpoint.
            revenue += endpoint_revenue(traits, calf_sex, economics, rng)
        # Stash this heifer's saleable value in case she is not retained.
        if system.heifer_retention and calf_sex == "F":
            heifer_pool[-1].sale_value = endpoint_revenue(
                traits, "F", economics, rng
            )

    # Costs - pasture cost scales with each cow's mature weight, which is
    # what gives MW a negative economic value.
    cost = herd_costs(herd, genetics, economics)

    # Age the herd; cull on age and on genetic stayability (STAY).
    survivors: list[_Cow] = []
    cull_revenue = 0.0
    for cow in herd:
        cow.age += 1
        stay_adj = cow.genetics.get("STAY", 0.0) / 100.0
        cull_p = min(0.95, max(0.0, system.replacement_rate - stay_adj))
        forced_out = cow.age > _MAX_COW_AGE or (
            cow.age > _FIRST_CALVING_AGE and rng.random() < cull_p
        )
        if forced_out:
            mw = genetics["MW"].mean + cow.genetics.get("MW", 0.0)
            cull_revenue += (mw / 100.0) * economics.cull_cow_price_per_cwt
        else:
            survivors.append(cow)

    next_herd = survivors

    if system.heifer_retention:
        # Fill exactly the openings the cull step created. Each retained
        # heifer incurs a development cost; each surplus heifer is instead
        # sold, realising her weaned-calf value.
        openings = max(0, system.herd_size - len(survivors))
        kept = heifer_pool[:openings]
        surplus = heifer_pool[openings:]
        # Surplus heifers are sold as weaned calves.
        for h in surplus:
            revenue += getattr(h, "sale_value", 0.0)
        # Retained heifers cost their development to first calving.
        cost += len(kept) * _REPLACEMENT_DEVELOPMENT_COST
        next_herd = survivors + kept
        # If the calf crop did not produce enough heifers, buy the rest.
        shortfall = system.herd_size - len(next_herd)
        if shortfall > 0:
            cost += shortfall * _PURCHASED_REPLACEMENT_COST
            for _ in range(shortfall):
                comp = _sample_composition(
                    system.cow_breed_composition, rng
                )
                next_herd.append(
                    _Cow(
                        age=_FIRST_CALVING_AGE,
                        genetics=_draw_genetics(genetics, rng, shift),
                        heterozygosity=_heterozygosity(comp.breeds),
                        breeds=dict(comp.breeds),
                    )
                )
    else:
        # Terminal herd: no heifers retained; top up by purchase.
        shortfall = system.herd_size - len(next_herd)
        if shortfall > 0:
            cost += shortfall * _PURCHASED_REPLACEMENT_COST
            for _ in range(shortfall):
                comp = _sample_composition(
                    system.cow_breed_composition, rng
                )
                next_herd.append(
                    _Cow(
                        age=_FIRST_CALVING_AGE,
                        genetics=_draw_genetics(genetics, rng, shift),
                        heterozygosity=_heterozygosity(comp.breeds),
                        breeds=dict(comp.breeds),
                    )
                )

    next_herd = next_herd[:system.herd_size]
    net = revenue + cull_revenue - cost
    return net, float(calves_weaned), next_herd
