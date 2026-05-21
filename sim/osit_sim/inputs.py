"""
Input models for the osit-sim herd-simulation engine.

These describe the production system, the economic environment, and the
simulation controls — everything the user supplies before a simulation
runs. The vocabulary follows standard bio-economic terminology (sale
endpoints,
terminal vs. replacement-generating, AUM-based costs) so the model is
familiar to anyone who has used a herd bio-economic model.

Reference: NexGenIQ Phase 3 Part 3A Section 1.3.2; Part 3B Section 2.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# The traits the simulation tracks.
#
# The full economically relevant EPD set for a beef enterprise. Each trait
# is simulated with a direct and/or maternal genetic component, is wired
# into the herd dynamics or the economic layer so it actually moves profit,
# and is perturbed by the MEV engine. Trait codes match the osit-index
# registry so a derived MEV vector maps straight onto a breeding goal.
# ---------------------------------------------------------------------------
#: Trait codes the simulation models, with units.
SIMULATED_TRAITS: dict[str, str] = {
    # --- Growth -----------------------------------------------------------
    "BW": "lb",        # birth weight (dystocia driver)
    "WW": "lb",        # weaning weight (calf's direct growth)
    "YW": "lb",        # yearling weight
    "PWG": "lb",       # post-weaning gain (weaning -> yearling)
    # --- Maternal ---------------------------------------------------------
    "MILK": "lb",      # maternal milk (dam contribution to calf WW)
    "MW": "lb",        # mature cow weight (pasture-cost driver)
    # --- Fertility / longevity -------------------------------------------
    "CED": "%",        # calving ease direct (calf's effect)
    "CEM": "%",        # calving ease maternal (daughter's effect)
    "HP": "%",         # heifer pregnancy
    "SC": "cm",        # scrotal circumference (sire fertility)
    "STAY": "%",       # stayability (cow remains productive)
    # --- Carcass ----------------------------------------------------------
    "CW": "lb",        # carcass weight
    "MARB": "score",   # marbling score
    "REA": "sq in",    # ribeye area
    "FAT": "in",       # backfat thickness
    # --- Feed efficiency --------------------------------------------------
    "DMI": "lb/day",   # dry-matter intake (feed cost driver)
    "RFI": "lb/day",   # residual feed intake (efficiency)
    # --- Temperament ------------------------------------------------------
    "DOC": "score",    # docility (shrink / performance / handling)
    # --- Health -----------------------------------------------------------
    "PAP": "mmHg",     # pulmonary arterial pressure (altitude disease)
}

#: Traits whose EPD is published only by certain breed associations. A
#: simulation only perturbs a restricted trait when the herd contains a
#: breed that publishes it (see ``traits_for_herd``).
BREED_RESTRICTED_TRAITS: dict[str, tuple[str, ...]] = {
    "PAP": ("Angus", "Simmental"),
}


class SaleEndpoint(str, Enum):
    """Where the calf crop is marketed (Phase 2 Section 1.3.1).

    The endpoint determines which traits carry economic value and how
    revenue is computed.
    """

    WEANING = "weaning"            # sold at weaning
    BACKGROUND = "background"      # sold after a backgrounding period
    FED = "fed"                    # sold finished, live, off the feedlot
    CARCASS = "carcass"            # sold on the rail, valued on a grid


@dataclass
class BreedComposition:
    """One breed-composition class within the herd.

    Attributes
    ----------
    fraction:
        The fraction of the herd (or bull battery) that is of this
        composition. Fractions across all classes sum to 1.
    breeds:
        Mapping of breed name -> breed fraction (summing to 1) for an
        animal of this class. A purebred Angus class is ``{"Angus": 1.0}``;
        an Angus-Hereford F1 is ``{"Angus": 0.5, "Hereford": 0.5}``.
    """

    fraction: float
    breeds: dict[str, float]


@dataclass
class ProductionSystem:
    """A description of the commercial cow-calf enterprise.

    Attributes
    ----------
    name:
        Human-readable label.
    herd_size:
        Target number of breeding cows.
    conception_rate:
        Probability a cow conceives during the breeding season.
    calving_loss_rate:
        Probability a pregnancy is lost between conception and weaning
        (abortion, dystocia loss, calf death).
    replacement_rate:
        Fraction of the cow herd replaced each year (= the cull rate at
        equilibrium). Retained heifers fill these slots when the index is
        not terminal.
    heifer_retention:
        ``True`` if the operation keeps its own replacement heifers
        (a self-replacing herd); ``False`` for a terminal operation.
    cow_breed_composition:
        Breed makeup of the cow herd.
    bull_breed_composition:
        Breed makeup of the bull battery the cows are mated to.
    """

    name: str
    herd_size: int = 250
    conception_rate: float = 0.92
    calving_loss_rate: float = 0.06
    replacement_rate: float = 0.18
    heifer_retention: bool = True
    cow_breed_composition: list[BreedComposition] = field(
        default_factory=lambda: [
            BreedComposition(1.0, {"Angus": 1.0})
        ]
    )
    bull_breed_composition: list[BreedComposition] = field(
        default_factory=lambda: [
            BreedComposition(1.0, {"Angus": 1.0})
        ]
    )

    def __post_init__(self) -> None:
        for label, comps in (
            ("cow", self.cow_breed_composition),
            ("bull", self.bull_breed_composition),
        ):
            total = sum(c.fraction for c in comps)
            if abs(total - 1.0) > 1e-6:
                raise ValueError(
                    f"{label} breed-composition fractions must sum to 1, "
                    f"got {total:.4f}."
                )
        for rate_name in ("conception_rate", "calving_loss_rate",
                          "replacement_rate"):
            rate = getattr(self, rate_name)
            if not 0.0 <= rate <= 1.0:
                raise ValueError(
                    f"{rate_name} must be in [0, 1], got {rate}."
                )
        if self.herd_size < 1:
            raise ValueError("herd_size must be at least 1.")


@dataclass
class PriceBand:
    """A sale price for one weight range and sex class.

    Cattle are priced differently by weight and sex; the engine looks up an
    animal's price from the band whose ``[low, high)`` weight range and sex
    it falls into.

    Attributes
    ----------
    sex:
        ``"S"`` steer, ``"F"`` heifer, ``"C"`` cull cow.
    low, high:
        The weight range, in pounds.
    price_per_cwt:
        Price in dollars per hundredweight (100 lb).
    """

    sex: str
    low: float
    high: float
    price_per_cwt: float


@dataclass
class GridCell:
    """One premium/discount cell of a carcass pricing grid.

    Carcass cattle are priced on a quality-grade x yield-grade grid
    (Phase 2 Section 1.3.1).

    Attributes
    ----------
    quality_grade:
        ``"Prime"``, ``"Choice"``, ``"Select"`` or ``"Standard"``.
    yield_grade:
        Integer yield grade 1-5.
    premium:
        Premium (positive) or discount (negative), dollars per cwt of
        carcass, relative to the carcass base price.
    """

    quality_grade: str
    yield_grade: int
    premium: float


@dataclass
class EconomicScenario:
    """The economic environment the herd operates in.

    Attributes
    ----------
    name:
        Human-readable label.
    sale_endpoint:
        Where the calf crop is marketed.
    price_bands:
        Sale prices by weight/sex class (used for live sales).
    carcass_base_price:
        Base carcass price, dollars per cwt (used for the CARCASS
        endpoint).
    grid:
        Carcass grid premiums/discounts (CARCASS endpoint).
    cull_cow_price_per_cwt:
        Price received for cull cows, dollars per cwt.
    aum_cost:
        Cost of one animal-unit-month of pasture, in dollars — the cow-herd
        carrying cost.
    feed_cost_per_lb_dm:
        Feedlot/backgrounding feed cost, dollars per pound of dry matter.
    background_days:
        Days calves are backgrounded (BACKGROUND, FED, CARCASS endpoints).
    days_on_feed:
        Days on feed in the feedlot (FED, CARCASS endpoints).
    fixed_cost_per_cow:
        Annual non-feed fixed cost per cow (labour, health, overhead).
    discount_rate:
        Annual discount rate for net-present-value accumulation.
    elevation_ft:
        Elevation of the production environment, in feet above sea level.
        This drives the economic importance of PAP (pulmonary arterial
        pressure): high-altitude disease (brisket disease / bovine
        pulmonary hypertension) causes essentially no loss at low
        elevation and rising death loss and forced culling above roughly
        5,000 ft. At low elevation PAP's marginal economic value is near
        zero; in a high-mountain environment it can dominate the goal.
    replacement_development_cost:
        Cost to rear an own heifer from weaning to first calving.
    purchased_replacement_cost:
        Cost to buy a bred replacement female on the open market.
    value_of_lost_animal:
        Economic loss when a productive cow dies (e.g. to
        high-altitude disease) rather than being culled for salvage.
    """

    name: str
    sale_endpoint: SaleEndpoint = SaleEndpoint.WEANING
    price_bands: list[PriceBand] = field(default_factory=list)
    carcass_base_price: float = 300.0
    grid: list[GridCell] = field(default_factory=list)
    cull_cow_price_per_cwt: float = 110.0
    aum_cost: float = 38.0
    feed_cost_per_lb_dm: float = 0.16
    background_days: int = 0
    days_on_feed: int = 0
    fixed_cost_per_cow: float = 180.0
    discount_rate: float = 0.06
    elevation_ft: float = 0.0
    # Replacement-female and death-loss costs. These were previously
    # fixed model assumptions inside the herd engine; they are exposed
    # here so a user can set them to their own operation. The defaults
    # are representative North American figures, not authoritative
    # published values - a user who knows their own numbers should
    # override them.
    replacement_development_cost: float = 900.0
    purchased_replacement_cost: float = 1800.0
    value_of_lost_animal: float = 1400.0

    @property
    def altitude_stress(self) -> float:
        """Return the altitude-stress factor in [0, 1] for PAP economics.

        High-altitude disease is negligible below ~5,000 ft, then its
        pressure on the herd rises with elevation. The factor ramps
        linearly from 0 at 5,000 ft to 1 at 10,000 ft and is clamped
        outside that band. PAP's economic effects (death loss, culling)
        are all scaled by this factor, so PAP carries weight only where
        the environment makes it matter.
        """
        low, high = 5000.0, 10000.0
        if self.elevation_ft <= low:
            return 0.0
        if self.elevation_ft >= high:
            return 1.0
        return (self.elevation_ft - low) / (high - low)

    def price_for(self, sex: str, weight: float) -> float:
        """Return the per-cwt price for a live animal of ``sex``/``weight``.

        Falls back to the nearest band if the weight is outside every
        defined range, so the simulation never fails on an extreme animal.
        """
        bands = [b for b in self.price_bands if b.sex == sex]
        if not bands:
            return 0.0
        for b in bands:
            if b.low <= weight < b.high:
                return b.price_per_cwt
        # Outside all ranges: clamp to the closest band by weight.
        return min(
            bands,
            key=lambda b: min(
                abs(weight - b.low), abs(weight - b.high)
            ),
        ).price_per_cwt

    def grid_premium(self, quality: str, yield_grade: int) -> float:
        """Return the grid premium/discount for a carcass, or 0 if absent."""
        for cell in self.grid:
            if cell.quality_grade == quality and (
                cell.yield_grade == yield_grade
            ):
                return cell.premium
        return 0.0


@dataclass
class SimulationControls:
    """Controls governing how the simulation is run.

    Attributes
    ----------
    burn_in_years:
        Years simulated before the measured period, so the cow age
        distribution stabilises (Phase 3 Part 3B Section 2.5.1). Skipped
        for terminal systems where age structure is fixed.
    planning_horizon_years:
        Years over which discounted net return is accumulated.
    replicates:
        Number of independent simulated herds. The MEV is the mean across
        replicates; more replicates reduce Monte-Carlo error.
    seed:
        Base RNG seed. Fixing it makes a run reproducible and enables the
        common-random-numbers technique in MEV derivation.
    """

    burn_in_years: int = 10
    planning_horizon_years: int = 20
    replicates: int = 12
    seed: int = 20260520

    def __post_init__(self) -> None:
        if self.planning_horizon_years < 1:
            raise ValueError("planning_horizon_years must be >= 1.")
        if self.replicates < 1:
            raise ValueError("replicates must be >= 1.")


def herd_breeds(system: "ProductionSystem") -> set[str]:
    """Return the set of breed names present anywhere in the herd or bulls."""
    breeds: set[str] = set()
    for comps in (system.cow_breed_composition,
                  system.bull_breed_composition):
        for comp in comps:
            breeds.update(comp.breeds)
    return breeds


def traits_for_herd(system: "ProductionSystem") -> list[str]:
    """Return the trait codes a simulation should perturb for this herd.

    Every breed-universal trait is included. A breed-restricted trait
    (e.g. PAP) is included only when the herd contains a breed that
    publishes an EPD for it - so a goal built for an all-Charolais herd
    will not contain PAP, which Charolais does not evaluate.
    """
    breeds = herd_breeds(system)
    available: list[str] = []
    for code in SIMULATED_TRAITS:
        restricted = BREED_RESTRICTED_TRAITS.get(code)
        if restricted is None or breeds & set(restricted):
            available.append(code)
    return available
