"""
Index Builder API endpoints for NexGenIQ.

These wrap the osit-index engine: build an index and rank animals, and run
a tornado sensitivity analysis. Both accept fully self-contained requests so
they support the researcher batch-run use case (Phase 3 Part 3C Section
3.4).

Every successful build writes a reproducibility-ledger row (Phase 2 gap
G10) recording exactly what produced the result.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.services.audit import record_event
from app.core.config import get_settings
from app.core.database import get_db
from app.models import AdjustmentFactorTable, GeneticParameterSet, RunLedger, User
from app.schemas import (
    IndexBuildRequest,
    IndexBuildResponse,
    PhenotypeBuildRequest,
    SensitivityRequest,
    SensitivityResponse,
)
from app.services import index_service
from osit_index.phenotype import PhenotypeInputError

router = APIRouter(prefix="/index", tags=["index"])
_settings = get_settings()


def _load_parameter_set(db: Session, parameter_set_id: str | None):
    """Load a stored parameter set, or None for the built-in library."""
    if parameter_set_id is None:
        return None
    row = db.get(GeneticParameterSet, parameter_set_id)
    if row is None:
        return None
    return index_service.parameter_set_from_blob(
        row.name, row.version, row.data
    )


def _load_adjustment_table(db: Session, table_id: str | None):
    """Load a stored adjustment-factor table, or None."""
    if table_id is None:
        return None
    row = db.get(AdjustmentFactorTable, table_id)
    if row is None:
        return None
    return index_service.adjustment_table_from_blob(
        row.version, row.base_breed, row.factors
    )


@router.post("/build", response_model=IndexBuildResponse)
def build(
    request: IndexBuildRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IndexBuildResponse:
    """Build an economic selection index and rank the supplied animals.

    The request is self-contained: it carries the breeding goal, the
    candidate animals, and references to a stored parameter set and
    adjustment table (or uses the built-in defaults). The response carries
    the index weights, the ranked animals with confidence intervals and
    plain-language explanations, and the validation report.
    """
    parameter_set = _load_parameter_set(db, request.parameter_set_id)
    adjustment_table = _load_adjustment_table(
        db, request.adjustment_table_id
    )

    response = index_service.run_index_build(
        request,
        parameter_set=parameter_set,
        adjustment_table=adjustment_table,
    )

    # Reproducibility ledger: record what produced this result.
    ledger = RunLedger(
        engine_version=_settings.engine_version,
        param_set_version=(
            parameter_set.version if parameter_set else "consensus-built-in"
        ),
        adjustment_table_version=response.adjustment_table_version,
        mode=response.mode,
        inputs_summary={
            "goal": request.goal.name,
            "trait_count": len(request.goal.components),
            "animal_count": len(request.animals),
            # The EPD source evaluation(s) the animals came from -
            # provenance, so a recorded run is fully traceable.
            "epd_evaluations": sorted(
                {
                    a.evaluation_id
                    for a in request.animals
                    if a.evaluation_id
                }
            ),
        },
        result_summary={
            "ok": response.ok,
            "ranked": len(response.scores),
            "excluded": len(response.excluded),
            "errors": sum(
                1 for v in response.validation if v.severity == "error"
            ),
        },
        created_by=user.id,
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)

    response.ledger_id = ledger.id

    record_event(
        db, event_type="index_build",
        summary=(
            f"Built index '{request.goal.name}' "
            f"({len(request.goal.components)} traits, "
            f"{len(request.animals)} animals)."
        ),
        user=user,
    )
    return response


@router.post("/build-from-phenotypes", response_model=IndexBuildResponse)
def build_from_phenotypes(
    request: PhenotypeBuildRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IndexBuildResponse:
    """Build an index from raw performance records instead of EPDs.

    For producers who measure their own animals but have no EPDs. The
    request carries the breeding goal and a list of phenotype records
    (each with a contemporary-group label). The backend converts the
    records to estimated breeding values by mass selection -- within
    contemporary-group adjustment, EBV = h2 * deviation, accuracy
    sqrt(h2) -- then runs the standard index pipeline. The response is the
    same shape as an EPD build, with added validation notes making clear
    the ranking is own-performance-derived.
    """
    parameter_set = _load_parameter_set(db, request.parameter_set_id)
    adjustment_table = _load_adjustment_table(
        db, request.adjustment_table_id
    )

    try:
        response = index_service.run_phenotype_index_build(
            request,
            parameter_set=parameter_set,
            adjustment_table=adjustment_table,
        )
    except PhenotypeInputError as exc:
        # Bad phenotype input (e.g. a missing contemporary group) is a
        # client error, not a server fault: return 400 with the engine's
        # plain-language message so the producer can fix their upload.
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ledger = RunLedger(
        engine_version=_settings.engine_version,
        param_set_version=(
            parameter_set.version if parameter_set else "consensus-built-in"
        ),
        adjustment_table_version=response.adjustment_table_version,
        mode=response.mode,
        inputs_summary={
            "goal": request.goal.name,
            "trait_count": len(request.goal.components),
            "animal_count": len(request.records),
            "input_type": "phenotype",
            "epd_evaluations": ["own-performance (phenotype)"],
            "contemporary_groups": sorted(
                {r.contemporary_group for r in request.records}
            ),
        },
        result_summary={
            "ok": response.ok,
            "ranked": len(response.scores),
            "excluded": len(response.excluded),
            "errors": sum(
                1 for v in response.validation if v.severity == "error"
            ),
        },
        created_by=user.id,
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)

    response.ledger_id = ledger.id
    return response


@router.post("/sensitivity", response_model=SensitivityResponse)
def sensitivity(
    request: SensitivityRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SensitivityResponse:
    """Run a one-at-a-time (tornado) sensitivity analysis on the index.

    Each economic weight is perturbed up and down by ``variation`` and the
    ranking stability is reported, with a plain-language summary.
    """
    parameter_set = _load_parameter_set(db, request.parameter_set_id)
    adjustment_table = _load_adjustment_table(
        db, request.adjustment_table_id
    )
    return index_service.run_sensitivity(
        request,
        parameter_set=parameter_set,
        adjustment_table=adjustment_table,
    )
