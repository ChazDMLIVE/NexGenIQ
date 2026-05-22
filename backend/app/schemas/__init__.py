"""
Pydantic request/response schemas for the NexGenIQ API.

These define the JSON contract of the REST API (Phase 3 Part 3C Section
3.4). They are deliberately separate from the SQLAlchemy ORM models: the
API contract can evolve independently of the storage schema, and FastAPI
uses these for automatic validation and OpenAPI documentation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
    role: str = "producer"


class UserOut(BaseModel):
    """A user as returned by the API (never includes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool


class Token(BaseModel):
    """An issued JWT access token."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Traits and parameters
# ---------------------------------------------------------------------------
class TraitOut(BaseModel):
    """A trait registry entry."""

    code: str
    name: str
    category: str
    units: str
    higher_is_better: bool
    is_threshold: bool
    # Breed associations that publish this trait's EPD. Empty means
    # the trait is breed-universal; a non-empty list (e.g. PAP) means
    # the trait is only offered for herds containing those breeds.
    breeds: list[str] = Field(default_factory=list)
    description: str


# ---------------------------------------------------------------------------
# Breeding goal
# ---------------------------------------------------------------------------
class GoalComponentIn(BaseModel):
    """One trait + economic weight in a breeding goal."""

    trait_code: str
    economic_weight: float


class BreedingGoalIn(BaseModel):
    """Create/update payload for a breeding goal."""

    name: str
    basis: str = "per_cow_exposed"
    components: list[GoalComponentIn]
    source: str = "manual"


class BreedingGoalOut(BreedingGoalIn):
    """A stored breeding goal."""

    model_config = ConfigDict(from_attributes=True)

    id: str


# ---------------------------------------------------------------------------
# Animals
# ---------------------------------------------------------------------------
class EpdIn(BaseModel):
    """A single EPD value for an animal."""

    trait_code: str
    value: float
    bif_accuracy: float | None = None
    scale: str = "EPD"


class AnimalIn(BaseModel):
    """A candidate animal in an index request."""

    animal_id: str
    breed: str
    evaluation_id: str = ""
    sex: str = ""
    epds: list[EpdIn]


# ---------------------------------------------------------------------------
# Phenotype input (for producers with performance records but no EPDs)
# ---------------------------------------------------------------------------
class PhenotypeRecordIn(BaseModel):
    """One animal's raw, age-standardized performance records.

    ``phenotypes`` maps a producer-facing trait column (WW, YW, BW, IMF,
    REA, BF, DMI, RFI, DOC, PAP, LPAP) to its measured value. Every animal
    must carry a contemporary-group label so its performance is compared
    only within the group it was managed and measured with.
    """

    animal_id: str
    breed: str = "Angus"
    sex: str = ""
    contemporary_group: str
    phenotypes: dict[str, float]


class PhenotypeBuildRequest(BaseModel):
    """Build an index from phenotype records instead of EPDs.

    Identical to IndexBuildRequest except the candidate animals are given
    as raw performance records; the backend converts them to estimated
    breeding values (mass-selection: EBV = h2 * within-contemporary-group
    deviation, accuracy = sqrt(h2)) before running the standard index
    pipeline.
    """

    goal: BreedingGoalIn
    records: list[PhenotypeRecordIn]
    parameter_set_id: str | None = Field(
        default=None,
        description="Stored parameter set to use; null = built-in "
                    "consensus library.",
    )
    mode: str = Field(
        default="economic_weight",
        description="economic_weight | blup_index",
    )
    missing_policy: str = Field(
        default="exclude", description="exclude | impute"
    )
    adjustment_table_id: str | None = None
    native_multi_breed: bool = False


# ---------------------------------------------------------------------------
# Index build request / response
# ---------------------------------------------------------------------------
class IndexBuildRequest(BaseModel):
    """A full, self-contained request to build an index and rank animals.

    The request carries everything the engine needs, so it can be used
    statelessly (the researcher batch-run use case) without first creating
    stored scenario/dataset records.
    """

    goal: BreedingGoalIn
    animals: list[AnimalIn]
    parameter_set_id: str | None = Field(
        default=None,
        description="Stored parameter set to use; null = built-in "
                    "consensus library.",
    )
    mode: str = Field(
        default="economic_weight",
        description="economic_weight | blup_index",
    )
    missing_policy: str = Field(
        default="exclude", description="exclude | impute"
    )
    adjustment_table_id: str | None = None
    native_multi_breed: bool = False


class ValidationIssueOut(BaseModel):
    """A validation finding surfaced to the client."""

    severity: str
    code: str
    message: str
    fix_hint: str = ""
    location: str = ""


class AnimalScoreOut(BaseModel):
    """One animal's index result."""

    rank: int
    animal_id: str
    breed: str
    index_value: float
    std_error: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    contributions: dict[str, float]
    is_partial: bool
    explanation: str = ""


class InterpretationOut(BaseModel):
    """A layered, plain-language interpretation of a result.

    Shared by the index build and the herd simulation. The interpretation
    is informational decision-support; the ``disclaimer`` field states
    explicitly that it is not a recommendation to take any action.
    """

    headline: str = ""
    readout: str = ""
    detail: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    disclaimer: str = ""


class IndexBuildResponse(BaseModel):
    """The full response of an index build."""

    ok: bool
    mode: str
    weights: dict[str, float]
    scores: list[AnimalScoreOut]
    excluded: list[str]
    validation: list[ValidationIssueOut]
    adjustment_table_version: str
    ledger_id: str | None = None
    interpretation: InterpretationOut = Field(
        default_factory=InterpretationOut
    )


# ---------------------------------------------------------------------------
# Sensitivity
# ---------------------------------------------------------------------------
class SensitivityRequest(IndexBuildRequest):
    """An index build plus a perturbation size for tornado sensitivity."""

    variation: float = 0.20


class TornadoEntryOut(BaseModel):
    """Sensitivity of the ranking to one economic weight."""

    trait_code: str
    rank_corr_low: float
    rank_corr_high: float
    top_changed: bool


class SensitivityResponse(BaseModel):
    """The result of a tornado sensitivity analysis."""

    baseline_top: str
    summary: str
    entries: list[TornadoEntryOut]


# ---------------------------------------------------------------------------
# Herd-simulation schemas (Milestone 2)
# ---------------------------------------------------------------------------
class BreedCompositionIn(BaseModel):
    """One breed-composition class within the herd or bull battery."""

    fraction: float = Field(ge=0.0, le=1.0)
    breeds: dict[str, float]


class ProductionSystemIn(BaseModel):
    """A description of the commercial cow-calf enterprise."""

    name: str
    herd_size: int = Field(default=250, ge=1)
    conception_rate: float = Field(default=0.92, ge=0.0, le=1.0)
    calving_loss_rate: float = Field(default=0.06, ge=0.0, le=1.0)
    replacement_rate: float = Field(default=0.18, ge=0.0, le=1.0)
    heifer_retention: bool = True
    cow_breed_composition: list[BreedCompositionIn]
    bull_breed_composition: list[BreedCompositionIn]


class PriceBandIn(BaseModel):
    """A sale price for one weight range and sex class."""

    sex: str
    low: float
    high: float
    price_per_cwt: float


class GridCellIn(BaseModel):
    """One premium/discount cell of a carcass pricing grid."""

    quality_grade: str
    yield_grade: int
    premium: float


class EconomicScenarioIn(BaseModel):
    """The economic environment the herd operates in."""

    name: str
    sale_endpoint: str = "weaning"
    price_bands: list[PriceBandIn] = Field(default_factory=list)
    carcass_base_price: float = 300.0
    grid: list[GridCellIn] = Field(default_factory=list)
    cull_cow_price_per_cwt: float = 110.0
    aum_cost: float = 38.0
    feed_cost_per_lb_dm: float = 0.16
    background_days: int = 0
    days_on_feed: int = 0
    fixed_cost_per_cow: float = 180.0
    discount_rate: float = 0.06
    # Elevation of the production environment, feet above sea level.
    # Drives the economic importance of PAP (high-altitude / brisket
    # disease): near-zero effect below ~5,000 ft, rising loss above it.
    elevation_ft: float = Field(default=0.0, ge=0.0, le=14000.0)
    # Replacement-female and death-loss costs (defaults are
    # representative figures; a user can set them to their operation).
    replacement_development_cost: float = Field(default=900.0, ge=0.0)
    purchased_replacement_cost: float = Field(default=1800.0, ge=0.0)
    value_of_lost_animal: float = Field(default=1400.0, ge=0.0)
    # High-altitude (PAP / brisket) disease economics. The death-loss
    # rate is the producer's observed annual herd death loss to the
    # disease; the model calibrates its PAP curve to it.
    pap_death_loss_rate: float = Field(default=0.02, ge=0.0, le=0.5)
    pap_proactive_culling: bool = True


class SimulationControlsIn(BaseModel):
    """Controls governing how the simulation is run."""

    burn_in_years: int = Field(default=10, ge=0)
    planning_horizon_years: int = Field(default=20, ge=1)
    replicates: int = Field(default=12, ge=1, le=60)
    seed: int = 20260520


class SimulationRequest(BaseModel):
    """A full, self-contained request to derive economic values."""

    production_system: ProductionSystemIn
    economic_scenario: EconomicScenarioIn
    controls: SimulationControlsIn = Field(
        default_factory=SimulationControlsIn
    )
    traits: list[str] = Field(
        default_factory=list,
        description="Trait subset to derive MEVs for; empty = all.",
    )


class DerivedMevOut(BaseModel):
    """One derived marginal economic value."""

    trait_code: str
    units: str
    mev: float
    mc_std_error: float
    is_precise: bool


class SimulationResponse(BaseModel):
    """The result of an MEV-derivation run.

    The ``mevs`` list converts directly into an Index Builder breeding
    goal — the integration seam between the two engines.
    """

    baseline_profit: float
    replicates: int
    mevs: list[DerivedMevOut]
    warnings: list[str]
    interpretation: InterpretationOut = Field(
        default_factory=InterpretationOut
    )

# ---------------------------------------------------------------------------
# Economic-value estimator (for users who do not run the herd simulation)
# ---------------------------------------------------------------------------
class EstimatorQuestionOut(BaseModel):
    """One plain-language question in a trait's economic-value recipe."""

    key: str
    prompt: str
    help_text: str
    default: float
    units: str
    minimum: float
    maximum: float


class EstimatorRecipeOut(BaseModel):
    """A trait's economic-value recipe: its questions and its formula."""

    trait_code: str
    questions: list[EstimatorQuestionOut]
    formula_text: str
    basis_note: str


class EstimateRequest(BaseModel):
    """A request to estimate the economic value of one trait."""

    trait_code: str
    answers: dict[str, float] = Field(default_factory=dict)


class EstimateResultOut(BaseModel):
    """The estimated economic value for one trait."""

    trait_code: str
    economic_value: float
    formula_text: str
    basis_note: str
    inputs_used: dict[str, float]


# ---------------------------------------------------------------------------
# Saved work - items a user has explicitly chosen to keep
# ---------------------------------------------------------------------------
class SavedItemCreate(BaseModel):
    """A request to save a piece of work."""

    # One of: "index_result", "simulation_result", "breeding_goal".
    kind: str
    name: str = Field(min_length=1, max_length=200)
    # The full inputs + result, in the shape the tool re-opens it with.
    payload: dict = Field(default_factory=dict)


class SavedItemSummary(BaseModel):
    """A saved item without its payload - for the list view."""

    id: str
    kind: str
    name: str
    created_at: str


class SavedItemOut(SavedItemSummary):
    """A full saved item, including the payload, for re-opening."""

    payload: dict
