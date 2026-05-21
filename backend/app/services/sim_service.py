"""
Simulation service — the bridge between the REST API and the osit-sim
herd-simulation engine.

This module converts API request schemas into osit-sim domain objects,
runs the MEV-derivation engine, and converts the result back into API
response schemas. It is the simulation-side counterpart of
:mod:`app.services.index_service`, keeping the engine free of web concerns
(Phase 3 Part 3C Section 3.2.3).

Its key output — a vector of derived marginal economic values — is exactly
the economic-weight input the Index Builder's breeding goal expects. That
shared shape is the integration seam between the two engines.
"""

from __future__ import annotations

from osit_sim import (
    BreedComposition,
    EconomicScenario,
    GridCell,
    PriceBand,
    ProductionSystem,
    SaleEndpoint,
    SimulationControls,
    default_herd_genetics,
    derive_mevs,
    interpret_mev_result,
)

from app import schemas

# --- enum mapping ----------------------------------------------------------
_ENDPOINTS = {
    "weaning": SaleEndpoint.WEANING,
    "background": SaleEndpoint.BACKGROUND,
    "fed": SaleEndpoint.FED,
    "carcass": SaleEndpoint.CARCASS,
}


# ---------------------------------------------------------------------------
# Request -> engine objects
# ---------------------------------------------------------------------------
def production_system_from_schema(
    s: schemas.ProductionSystemIn,
) -> ProductionSystem:
    """Build an engine :class:`ProductionSystem` from its API schema."""
    return ProductionSystem(
        name=s.name,
        herd_size=s.herd_size,
        conception_rate=s.conception_rate,
        calving_loss_rate=s.calving_loss_rate,
        replacement_rate=s.replacement_rate,
        heifer_retention=s.heifer_retention,
        cow_breed_composition=[
            BreedComposition(c.fraction, dict(c.breeds))
            for c in s.cow_breed_composition
        ],
        bull_breed_composition=[
            BreedComposition(c.fraction, dict(c.breeds))
            for c in s.bull_breed_composition
        ],
    )


def economic_scenario_from_schema(
    s: schemas.EconomicScenarioIn,
) -> EconomicScenario:
    """Build an engine :class:`EconomicScenario` from its API schema."""
    return EconomicScenario(
        name=s.name,
        sale_endpoint=_ENDPOINTS.get(
            s.sale_endpoint, SaleEndpoint.WEANING
        ),
        price_bands=[
            PriceBand(b.sex, b.low, b.high, b.price_per_cwt)
            for b in s.price_bands
        ],
        carcass_base_price=s.carcass_base_price,
        grid=[
            GridCell(g.quality_grade, g.yield_grade, g.premium)
            for g in s.grid
        ],
        cull_cow_price_per_cwt=s.cull_cow_price_per_cwt,
        aum_cost=s.aum_cost,
        feed_cost_per_lb_dm=s.feed_cost_per_lb_dm,
        background_days=s.background_days,
        days_on_feed=s.days_on_feed,
        fixed_cost_per_cow=s.fixed_cost_per_cow,
        discount_rate=s.discount_rate,
        elevation_ft=s.elevation_ft,
        replacement_development_cost=s.replacement_development_cost,
        purchased_replacement_cost=s.purchased_replacement_cost,
        value_of_lost_animal=s.value_of_lost_animal,
        pap_death_loss_rate=s.pap_death_loss_rate,
        pap_proactive_culling=s.pap_proactive_culling,
    )


def controls_from_schema(
    s: schemas.SimulationControlsIn,
) -> SimulationControls:
    """Build engine :class:`SimulationControls` from its API schema."""
    return SimulationControls(
        burn_in_years=s.burn_in_years,
        planning_horizon_years=s.planning_horizon_years,
        replicates=s.replicates,
        seed=s.seed,
    )


# ---------------------------------------------------------------------------
# Top-level operation
# ---------------------------------------------------------------------------
def run_mev_derivation(
    request: schemas.SimulationRequest,
) -> schemas.SimulationResponse:
    """Run a herd simulation and derive marginal economic values.

    Parameters
    ----------
    request:
        The validated API request — a production system, an economic
        scenario, simulation controls, and an optional trait subset.

    Returns
    -------
    schemas.SimulationResponse
        The derived MEVs (with Monte-Carlo errors), the baseline herd
        profit, and any warnings. The MEV list is directly convertible
        into an Index Builder breeding goal.
    """
    system = production_system_from_schema(request.production_system)
    economics = economic_scenario_from_schema(request.economic_scenario)
    controls = controls_from_schema(request.controls)

    result = derive_mevs(
        system,
        economics,
        controls,
        default_herd_genetics(),
        traits=request.traits or None,
    )

    interp = interpret_mev_result(result)

    return schemas.SimulationResponse(
        baseline_profit=result.baseline_profit,
        replicates=result.replicates,
        interpretation=schemas.InterpretationOut(
            headline=interp.headline,
            readout=interp.readout,
            detail=interp.detail,
            cautions=interp.cautions,
            disclaimer=interp.disclaimer,
        ),
        mevs=[
            schemas.DerivedMevOut(
                trait_code=m.trait_code,
                units=m.units,
                mev=m.mev,
                mc_std_error=m.mc_std_error,
                is_precise=m.is_precise,
            )
            for m in result.mevs
        ],
        warnings=result.warnings,
    )
