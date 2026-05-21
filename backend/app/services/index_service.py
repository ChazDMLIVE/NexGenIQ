"""
Index service — the bridge between the REST API and the osit-index engine.

This module converts API request schemas into osit-index domain objects,
invokes the engine, and converts the engine's results back into API
response schemas. It is the only place that knows both the wire format and
the engine's object model, keeping the engine itself free of any web
concern (Phase 3 Part 3C Section 3.2.3).
"""

from __future__ import annotations

from osit_index import (
    Animal,
    AnimalSet,
    BreedingGoal,
    EconomicBasis,
    GeneticParameterSet,
    GoalComponent,
    TraitParameters,
    build_index,
    consensus_parameter_set,
    example_adjustment_table,
    explain_score,
    interpret_index_result,
    tornado_sensitivity,
)
from osit_index.adjustment import AdjustmentFactorTable
from osit_index.animal import EpdScale, EpdValue
from osit_index.index import IndexMode, MissingEpdPolicy

from app import schemas

# --- enum mapping ----------------------------------------------------------
_MODES = {
    "economic_weight": IndexMode.ECONOMIC_WEIGHT,
    "blup_index": IndexMode.BLUP_INDEX,
}
_POLICIES = {
    "exclude": MissingEpdPolicy.EXCLUDE,
    "impute": MissingEpdPolicy.IMPUTE_MEAN,
}
_BASES = {
    "per_cow_exposed": EconomicBasis.PER_COW_EXPOSED,
    "per_calf": EconomicBasis.PER_CALF,
    "per_unit": EconomicBasis.PER_UNIT,
}


# ---------------------------------------------------------------------------
# Request -> engine objects
# ---------------------------------------------------------------------------
def goal_from_schema(goal: schemas.BreedingGoalIn) -> BreedingGoal:
    """Build an engine :class:`BreedingGoal` from its API schema."""
    return BreedingGoal(
        name=goal.name,
        basis=_BASES.get(goal.basis, EconomicBasis.PER_COW_EXPOSED),
        components=[
            GoalComponent(c.trait_code, c.economic_weight)
            for c in goal.components
        ],
        source=goal.source,
    )


def animal_set_from_schema(animals: list[schemas.AnimalIn]) -> AnimalSet:
    """Build an engine :class:`AnimalSet` from the API animal list."""
    engine_animals = []
    for a in animals:
        epds = {
            e.trait_code: EpdValue(
                trait_code=e.trait_code,
                value=e.value,
                bif_accuracy=e.bif_accuracy,
                scale=EpdScale.EBV if e.scale == "EBV" else EpdScale.EPD,
            )
            for e in a.epds
        }
        engine_animals.append(
            Animal(
                animal_id=a.animal_id,
                breed=a.breed,
                epds=epds,
                evaluation_id=a.evaluation_id,
                sex=a.sex,
            )
        )
    return AnimalSet(animals=engine_animals)


def parameter_set_from_blob(
    name: str, version: str, data: dict
) -> GeneticParameterSet:
    """Reconstruct an engine parameter set from a stored JSON blob.

    The blob shape is ``{"traits": {code: {h2, sd, citation}},
    "correlations": [[code_a, code_b, r_g], ...]}``.
    """
    trait_params = {
        code: TraitParameters(
            trait_code=code,
            heritability=tp["h2"],
            genetic_sd=tp["sd"],
            citation=tp.get("citation", ""),
        )
        for code, tp in data.get("traits", {}).items()
    }
    correlations = {
        frozenset({a, b}): r
        for a, b, r in data.get("correlations", [])
    }
    return GeneticParameterSet(
        name=name,
        version=version,
        trait_params=trait_params,
        genetic_correlations=correlations,
    )


def adjustment_table_from_blob(
    version: str, base_breed: str, factors: dict
) -> AdjustmentFactorTable:
    """Reconstruct an engine adjustment table from a stored JSON blob.

    The stored blob keys factors as ``"breed|trait"`` strings (JSON cannot
    use tuple keys); this splits them back into tuples.
    """
    tuple_factors = {
        tuple(key.split("|", 1)): value
        for key, value in factors.items()
    }
    return AdjustmentFactorTable(
        version=version, base_breed=base_breed, factors=tuple_factors
    )


# ---------------------------------------------------------------------------
# Engine result -> response schema
# ---------------------------------------------------------------------------
def _validation_out(report) -> list[schemas.ValidationIssueOut]:
    """Convert an engine validation report to response schema."""
    return [
        schemas.ValidationIssueOut(
            severity=i.severity.value,
            code=i.code,
            message=i.message,
            fix_hint=i.fix_hint,
            location=i.location,
        )
        for i in report.issues
    ]


# ---------------------------------------------------------------------------
# Top-level operations
# ---------------------------------------------------------------------------
def run_index_build(
    request: schemas.IndexBuildRequest,
    *,
    parameter_set: GeneticParameterSet | None = None,
    adjustment_table: AdjustmentFactorTable | None = None,
) -> schemas.IndexBuildResponse:
    """Execute an index build and return the API response schema.

    Parameters
    ----------
    request:
        The validated API request.
    parameter_set:
        The genetic-parameter set to use; if ``None`` the built-in
        consensus library is used.
    adjustment_table:
        The across-breed adjustment table; if ``None`` and the animal set
        is multi-breed, the engine will require one (or a native-multi-breed
        declaration) and return a validation ERROR otherwise.
    """
    goal = goal_from_schema(request.goal)
    animal_set = animal_set_from_schema(request.animals)
    params = parameter_set or consensus_parameter_set()

    result = build_index(
        goal,
        params,
        animal_set,
        mode=_MODES.get(request.mode, IndexMode.ECONOMIC_WEIGHT),
        missing_policy=_POLICIES.get(
            request.missing_policy, MissingEpdPolicy.EXCLUDE
        ),
        adjustment_table=adjustment_table,
        native_multi_breed=request.native_multi_breed,
    )

    scores = [
        schemas.AnimalScoreOut(
            rank=s.rank,
            animal_id=s.animal_id,
            breed=s.breed,
            index_value=s.index_value,
            std_error=s.std_error,
            ci_low=s.ci_low,
            ci_high=s.ci_high,
            contributions=s.contributions,
            is_partial=s.is_partial,
            explanation=explain_score(s, result),
        )
        for s in result.scores
    ]

    interp = interpret_index_result(result)

    return schemas.IndexBuildResponse(
        ok=result.validation.ok,
        mode=result.mode.value,
        weights=result.weights,
        scores=scores,
        excluded=result.excluded,
        validation=_validation_out(result.validation),
        adjustment_table_version=result.adjustment_table_version,
        interpretation=schemas.InterpretationOut(
            headline=interp.headline,
            readout=interp.readout,
            detail=interp.detail,
            cautions=interp.cautions,
            disclaimer=interp.disclaimer,
        ),
    )


def run_sensitivity(
    request: schemas.SensitivityRequest,
    *,
    parameter_set: GeneticParameterSet | None = None,
    adjustment_table: AdjustmentFactorTable | None = None,
) -> schemas.SensitivityResponse:
    """Execute a tornado sensitivity analysis and return the response."""
    goal = goal_from_schema(request.goal)
    animal_set = animal_set_from_schema(request.animals)
    params = parameter_set or consensus_parameter_set()

    result = tornado_sensitivity(
        goal,
        params,
        animal_set,
        variation=request.variation,
        mode=_MODES.get(request.mode, IndexMode.ECONOMIC_WEIGHT),
        missing_policy=_POLICIES.get(
            request.missing_policy, MissingEpdPolicy.EXCLUDE
        ),
        adjustment_table=adjustment_table,
        native_multi_breed=request.native_multi_breed,
    )

    return schemas.SensitivityResponse(
        baseline_top=result.baseline_top,
        summary=result.summary,
        entries=[
            schemas.TornadoEntryOut(
                trait_code=e.trait_code,
                rank_corr_low=e.rank_corr_low,
                rank_corr_high=e.rank_corr_high,
                top_changed=e.top_changed_low or e.top_changed_high,
            )
            for e in result.entries
        ],
    )
