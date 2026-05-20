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
def fast_controls():
    """Small simulation controls so tests run quickly but meaningfully."""
    return SimulationControls(
        burn_in_years=4,
        planning_horizon_years=6,
        replicates=4,
        seed=20260520,
    )
