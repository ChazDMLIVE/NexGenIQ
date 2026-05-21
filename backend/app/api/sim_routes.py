"""
Herd-simulation API endpoints for NexGenIQ (Milestone 2).

These wrap the osit-sim engine: run a whole-herd simulation and derive the
marginal economic values of the traits, which a user can then carry
straight into the Index Builder as a breeding goal.

A herd simulation is more expensive than an analytical index build, but for
the MVP it still completes within a normal request (a few seconds at the
default replicate count). The asynchronous job pattern specified in Phase 3
for very large runs is a later hardening step; the endpoint here is
synchronous and documents that.

Every derivation writes a reproducibility-ledger row recording the engine
version and the run controls (Phase 2 gap G10).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models import RunLedger, User
from app.schemas import SimulationRequest, SimulationResponse
from app.services import sim_service

router = APIRouter(prefix="/simulation", tags=["simulation"])
_settings = get_settings()


@router.post("/derive-mevs", response_model=SimulationResponse)
def derive_mevs(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SimulationResponse:
    """Run a whole-herd simulation and derive marginal economic values.

    The request describes a production system and an economic scenario;
    the response carries the derived economic value of each trait, its
    Monte-Carlo standard error, and the baseline herd profit.

    The returned MEV list is the economic-weight set for an Index Builder
    breeding goal — the user can carry it straight into the index workflow.
    """
    response = sim_service.run_mev_derivation(request)

    # Reproducibility ledger: record what produced this MEV set.
    ledger = RunLedger(
        engine_version="osit-sim 0.2.0",
        mode="mev_derivation",
        inputs_summary={
            "production_system": request.production_system.name,
            "herd_size": request.production_system.herd_size,
            "sale_endpoint": request.economic_scenario.sale_endpoint,
            "replicates": request.controls.replicates,
            "seed": request.controls.seed,
        },
        result_summary={
            "baseline_profit": response.baseline_profit,
            "traits": len(response.mevs),
            "imprecise": sum(
                1 for m in response.mevs if not m.is_precise
            ),
        },
        created_by=user.id,
    )
    db.add(ledger)
    db.commit()

    return response
