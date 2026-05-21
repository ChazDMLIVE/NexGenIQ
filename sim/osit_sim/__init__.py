"""
osit-sim — the NexGenIQ whole-herd bio-economic simulation engine.

This package is the second computational engine of NexGenIQ. It simulates a
beef cow-calf enterprise stochastically, year by year and animal by animal,
and derives the *marginal economic value* (MEV) of each trait by
finite-difference perturbation of the simulated profit function.

The MEV vector it produces is exactly the economic-weight input that the
`osit-index` engine consumes — that shared interface is the integration
seam of the two engines (Phase 3 Part 3C Section 3.2.3). A user can run the
full pipeline (describe the production system -> derive economic values ->
build an index -> rank animals) or use either engine standalone.

Methodology: NexGenIQ Phase 3 Part 3B Section 2.5, following the documented
bio-economic selection-index methodology. The engine performs no I/O and has
no web dependency, so it is independently testable.

Public API
----------
ProductionSystem    Herd structure, reproduction, breed composition.
EconomicScenario    Sale endpoint, prices, carcass grid, costs, horizon.
SimulationControls  Burn-in, planning horizon, replicates, RNG seed.
TraitGenetics       Per-trait genetic parameters for the simulated herd.
run_simulation      Simulate the herd and return baseline profit + summary.
derive_mevs         Derive the marginal economic value of every trait.
traits_for_herd     Breed-aware list of traits to evaluate for a herd.
"""

from .inputs import (
    ProductionSystem,
    EconomicScenario,
    SimulationControls,
    SaleEndpoint,
    BreedComposition,
    PriceBand,
    GridCell,
    SIMULATED_TRAITS,
    BREED_RESTRICTED_TRAITS,
    herd_breeds,
    traits_for_herd,
)
from .genetics import TraitGenetics, default_herd_genetics
from .herd import run_simulation, SimulationResult
from .mev import derive_mevs, MevResult, DerivedMev
from .interpret import interpret_mev_result, MevInterpretation

__version__ = "0.2.0"

__all__ = [
    "ProductionSystem",
    "EconomicScenario",
    "SimulationControls",
    "SaleEndpoint",
    "BreedComposition",
    "PriceBand",
    "GridCell",
    "SIMULATED_TRAITS",
    "BREED_RESTRICTED_TRAITS",
    "herd_breeds",
    "traits_for_herd",
    "TraitGenetics",
    "default_herd_genetics",
    "run_simulation",
    "SimulationResult",
    "derive_mevs",
    "MevResult",
    "DerivedMev",
    "interpret_mev_result",
    "MevInterpretation",
    "__version__",
]
