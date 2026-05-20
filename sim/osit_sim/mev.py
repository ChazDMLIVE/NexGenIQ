"""
Marginal economic value (MEV) derivation for osit-sim.

The economic value of a trait is the partial derivative of profit with
respect to that trait's genetic mean (Phase 1 Section 2.3). osit-sim
estimates that derivative numerically, by perturbing one trait's genetic
mean in the herd simulation and measuring the change in discounted profit.

Two techniques from Phase 3 Part 3B Section 2.5.2 make the estimate sound:

* Central finite difference - perturb the trait up and down and use the
  symmetric difference, which is second-order accurate.
* Common random numbers - the baseline and perturbed runs share the same
  RNG seed, so the difference reflects the perturbation, not Monte-Carlo
  noise.

Each MEV is averaged over independent replicate herds, and its Monte-Carlo
standard error is reported.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .genetics import TraitGenetics
from .herd import run_simulation
from .inputs import EconomicScenario, ProductionSystem, SimulationControls


@dataclass
class DerivedMev:
    """The derived marginal economic value of one trait.

    Attributes
    ----------
    trait_code:
        The trait.
    units:
        The trait's units.
    mev:
        Change in profit per one-unit improvement in the trait's genetic
        mean, on a per-cow-exposed, per-year basis.
    mc_std_error:
        Monte-Carlo standard error of the MEV estimate.
    """

    trait_code: str
    units: str
    mev: float
    mc_std_error: float

    @property
    def is_precise(self) -> bool:
        """Whether the Monte-Carlo error is small relative to the MEV."""
        if self.mev == 0.0:
            return True
        return abs(self.mc_std_error) <= 0.25 * abs(self.mev)


@dataclass
class MevResult:
    """The full result of an MEV-derivation run.

    Attributes
    ----------
    mevs:
        One DerivedMev per trait, ordered by descending absolute value.
    baseline_profit:
        Mean whole-herd annual profit of the unperturbed herd.
    replicates:
        How many replicate herds each MEV was averaged over.
    warnings:
        Plain-language warnings (e.g. an imprecise MEV).
    """

    mevs: list[DerivedMev] = field(default_factory=list)
    baseline_profit: float = 0.0
    replicates: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_economic_weights(self) -> dict[str, float]:
        """Return the MEVs as a trait_code -> weight mapping.

        This is exactly the shape the osit-index breeding goal expects -
        the integration seam between the two engines.
        """
        return {m.trait_code: m.mev for m in self.mevs}


def _annuity_factor(rate: float, years: int) -> float:
    """Present-value annuity factor for `years` at discount `rate`.

    Dividing a net-present total by this converts it to an equivalent
    level annual amount - the step that puts an MEV on a per-year basis.
    """
    if rate == 0.0:
        return float(years)
    return (1.0 - (1.0 + rate) ** (-years)) / rate * (1.0 + rate)


def _profit_at_shift(
    system: ProductionSystem,
    economics: EconomicScenario,
    controls: SimulationControls,
    genetics: dict[str, TraitGenetics],
    shift: dict[str, float],
    seed: int,
) -> float:
    """Profit for one herd run, normalised to a per-cow, per-year basis.

    The simulation accumulates discounted whole-herd profit over the
    planning horizon. An economic value is expressed per cow exposed per
    year (Phase 1 Section 2.3.2), so the net-present total is divided by
    the present-value annuity factor (multi-year discounted sum -> level
    annual equivalent) and by the herd size (whole-herd -> per-cow).
    """
    result = run_simulation(
        system, economics, controls, genetics,
        seed=seed, genetic_shift=shift,
    )
    annuity = _annuity_factor(
        economics.discount_rate, controls.planning_horizon_years
    )
    return result.net_present_profit / annuity / system.herd_size


def derive_mevs(
    system: ProductionSystem,
    economics: EconomicScenario,
    controls: SimulationControls,
    genetics: dict[str, TraitGenetics],
    *,
    traits: list[str] | None = None,
) -> MevResult:
    """Derive the marginal economic value of every (selected) trait.

    For each trait, the genetic mean is perturbed up and down by a small
    increment (a fraction of the trait's genetic SD). The herd simulation
    is re-run for each perturbation sharing the baseline's RNG seed
    (common random numbers), and the MEV is the central difference

        MEV = [ profit(mean + d) - profit(mean - d) ] / (2 * d)

    averaged over independent replicate herds.

    Parameters
    ----------
    system, economics, controls, genetics:
        The simulation inputs.
    traits:
        Which traits to derive an MEV for; defaults to every trait.

    Returns
    -------
    MevResult
        The derived MEVs with Monte-Carlo errors, ordered by importance.
    """
    trait_codes = traits if traits is not None else list(genetics)

    # Per-trait perturbation: a fraction of the genetic SD - small enough
    # to stay locally linear, large enough to exceed simulation noise.
    deltas = {code: 0.5 * genetics[code].genetic_sd for code in trait_codes}

    # Per-replicate seeds, derived from the base seed for reproducibility.
    rng = np.random.default_rng(controls.seed)
    rep_seeds = [
        int(rng.integers(1, 2 ** 31 - 1))
        for _ in range(controls.replicates)
    ]

    # Baseline profit per replicate (per cow-year). The reported baseline
    # scales it back to a whole-herd annual figure.
    baseline_per_cow = np.array([
        _profit_at_shift(system, economics, controls, genetics, {}, seed)
        for seed in rep_seeds
    ])
    baseline = baseline_per_cow * system.herd_size

    warnings: list[str] = []
    mevs: list[DerivedMev] = []

    for code in trait_codes:
        delta = deltas[code]
        per_rep_mev = np.empty(controls.replicates)

        for r, seed in enumerate(rep_seeds):
            # Common random numbers: both perturbed runs reuse seed[r].
            up = _profit_at_shift(
                system, economics, controls, genetics,
                {code: +delta}, seed,
            )
            down = _profit_at_shift(
                system, economics, controls, genetics,
                {code: -delta}, seed,
            )
            per_rep_mev[r] = (up - down) / (2.0 * delta)

        mev = float(per_rep_mev.mean())
        mc_se = (
            float(per_rep_mev.std(ddof=1) / np.sqrt(controls.replicates))
            if controls.replicates > 1
            else 0.0
        )

        derived = DerivedMev(
            trait_code=code,
            units=_units_for(code),
            mev=mev,
            mc_std_error=mc_se,
        )
        if not derived.is_precise:
            warnings.append(
                f"The economic value for {code} is imprecise "
                f"(Monte-Carlo error is large relative to it). Increase "
                f"the replicate count for a tighter estimate."
            )
        mevs.append(derived)

    mevs.sort(key=lambda m: abs(m.mev), reverse=True)

    return MevResult(
        mevs=mevs,
        baseline_profit=float(baseline.mean()),
        replicates=controls.replicates,
        warnings=warnings,
    )


def _units_for(code: str) -> str:
    """Return the units string for a trait code."""
    from .inputs import SIMULATED_TRAITS

    return SIMULATED_TRAITS.get(code, "unit")
