"""
Herd-simulation API endpoints for NexGenIQ (Milestone 2).

These wrap the osit-sim engine: run a whole-herd simulation and derive the
marginal economic values of the traits, which a user can then carry
straight into the Index Builder as a breeding goal.

A herd simulation is CPU-bound and runs for tens of seconds. To keep the
service responsive when several users run simulations at once, the number
of simulations running concurrently is capped (a semaphore). A request
that arrives while the cap is full gets an immediate, clear "server busy"
response (HTTP 503) rather than queueing behind long runs and dragging
every run down. The asynchronous job pattern specified in Phase 3 for very
large runs is a later hardening step; the endpoint here is synchronous.

Every derivation writes a reproducibility-ledger row recording the engine
version and the run controls (Phase 2 gap G10).
"""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models import RunLedger, User
from app.schemas import SimulationRequest, SimulationResponse
from app.services import sim_service
from app.services.audit import record_event

router = APIRouter(prefix="/simulation", tags=["simulation"])
_settings = get_settings()

# Concurrency cap. A bounded semaphore limits how many herd simulations
# run at once; its size comes from settings (roughly the number of CPU
# cores available to the backend). The endpoint acquires a slot WITHOUT
# blocking - if none is free, it returns a "server busy" response at once
# rather than letting the request pile up behind long-running simulations.
_sim_semaphore = threading.BoundedSemaphore(
    max(1, _settings.max_concurrent_simulations)
)


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
    breeding goal - the user can carry it straight into the index workflow.

    If the server is already running its maximum number of concurrent
    simulations, this returns HTTP 503 with a plain-language message so
    the caller can simply retry in a moment.
    """
    # Try to claim a simulation slot without waiting. A full cap means the
    # server is busy; tell the user clearly instead of queueing forever.
    if not _sim_semaphore.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The server is busy running other simulations right now. "
                "Please wait a moment and run it again - your inputs are "
                "still here."
            ),
        )
    try:
        response = sim_service.run_mev_derivation(request)
    finally:
        # Always free the slot, even if the simulation raised.
        _sim_semaphore.release()

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

    record_event(
        db, event_type="simulation_run",
        summary=(
            f"Ran herd simulation "
            f"'{request.production_system.name}' "
            f"({request.production_system.herd_size} cows, "
            f"{request.controls.replicates} replicates)."
        ),
        user=user,
    )
    return response
