"""Shared pytest fixtures for the osit-sim test suite."""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from osit_sim import (  # noqa: E402
    BreedComposition,
    EconomicScenario,
    GridCell,
    PriceBand,
    ProductionSystem,
    SaleEndpoint,
    SimulationControls,
    default_herd_genetics,
)


@pytest.fixture
def genetics():
    """The default per-trait herd genetics."""
    return default_herd_genetics()


@pytest.fixture
def maternal_system():
    """A self-replacing single-breed cow-calf operation."""
    return ProductionSystem(
        name="Self-replacing Angus herd",
        herd_size=120,
        conception_rate=0.92,
        calving_loss_rate=0.06,
        replacement_rate=0.18,
        heifer_retention=True,
        cow_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
    )


@pytest.fixture
def terminal_system():
    """A terminal operation — every calf sold, no heifers retained."""
    return ProductionSystem(
        name="Terminal herd",
        herd_size=120,
        heifer_retention=False,
        cow_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
    )


@pytest.fixture
def weaning_economics():
    """A weaning-sale economic scenario with simple price bands."""
    return EconomicScenario(
        name="Weaning sale",
        sale_endpoint=SaleEndpoint.WEANING,
        price_bands=[
            PriceBand("S", 0, 500, 200.0),
            PriceBand("S", 500, 600, 195.0),
            PriceBand("S", 600, 9999, 180.0),
            PriceBand("F", 0, 500, 185.0),
            PriceBand("F", 500, 600, 178.0),
            PriceBand("F", 600, 9999, 165.0),
        ],
        cull_cow_price_per_cwt=110.0,
        aum_cost=38.0,
        fixed_cost_per_cow=180.0,
        discount_rate=0.06,
    )


@pytest.fixture
def carcass_economics():
    """A carcass-grid economic scenario.

    Calves are backgrounded, fed, and sold on the rail valued against a
    USDA quality-grade x yield-grade grid - the endpoint at which the
    carcass traits (marbling, ribeye area, backfat, carcass weight) and
    feed efficiency carry their economic value.
    """
    return EconomicScenario(
        name="Carcass grid sale",
        sale_endpoint=SaleEndpoint.CARCASS,
        price_bands=[
            PriceBand("S", 0, 9999, 200.0),
            PriceBand("F", 0, 9999, 190.0),
            PriceBand("C", 0, 9999, 110.0),
        ],
        carcass_base_price=300.0,
        grid=[
            GridCell("Prime", 2, 24.0),
            GridCell("Prime", 3, 18.0),
            GridCell("Choice", 2, 6.0),
            GridCell("Choice", 3, 2.0),
            GridCell("Choice", 4, -8.0),
            GridCell("Select", 3, -14.0),
            GridCell("Select", 4, -22.0),
            GridCell("Standard", 3, -30.0),
        ],
        background_days=60,
        days_on_feed=160,
        feed_cost_per_lb_dm=0.16,
        cull_cow_price_per_cwt=110.0,
        aum_cost=38.0,
        fixed_cost_per_cow=180.0,
        discount_rate=0.06,
    )


@pytest.fixture
def fast_controls():
    """Small simulation controls so tests run quickly but meaningfully."""
    return SimulationControls(
        burn_in_years=4,
        planning_horizon_years=6,
        replicates=4,
        seed=20260520,
    )


@pytest.fixture
def sign_controls():
    """Controls for economic-sign sanity checks.

    Some traits (stayability, scrotal circumference, PAP) act through
    stochastic events - a cull, a conception, a death - so their MEV is a
    small number estimated from a noisy difference. Resolving its *sign*
    reliably needs more replicate herds than the quick ``fast_controls``
    fixture provides. This fixture trades a little test time for an MEV
    estimate precise enough to assert a sign on.
    """
    return SimulationControls(
        burn_in_years=4,
        planning_horizon_years=6,
        replicates=14,
        seed=20260520,
    )
