"""Shared pytest fixtures for the osit-index test suite."""

import os
import sys

import pytest

# Make the engine package importable when tests are run from anywhere.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from osit_index import (  # noqa: E402
    Animal,
    AnimalSet,
    BreedingGoal,
    EconomicBasis,
    GoalComponent,
    consensus_parameter_set,
)
from osit_index.animal import EpdValue  # noqa: E402


@pytest.fixture
def params():
    """The built-in consensus genetic-parameter set."""
    return consensus_parameter_set()


@pytest.fixture
def maternal_goal():
    """A small self-replacing-herd maternal goal: WW, CED, STAY."""
    return BreedingGoal(
        name="Self-replacing herd, weaning sale",
        basis=EconomicBasis.PER_COW_EXPOSED,
        components=[
            GoalComponent("WW", 0.85),
            GoalComponent("CED", 12.0),
            GoalComponent("STAY", 6.4),
        ],
        source="manual",
    )


@pytest.fixture
def angus_animals():
    """Five single-breed Angus candidates with full EPDs and accuracies."""
    rows = [
        # (id, WW, WW_acc, CED, CED_acc, STAY, STAY_acc)
        ("AAA-1842", 72.0, 0.85, 14.0, 0.70, 22.0, 0.55),
        ("AAA-1109", 60.0, 0.80, 8.0, 0.65, 18.0, 0.50),
        ("AAA-2204", 55.0, 0.75, 11.0, 0.60, 25.0, 0.45),
        ("AAA-0573", 80.0, 0.90, 4.0, 0.72, 12.0, 0.60),
        ("AAA-3318", 48.0, 0.70, 16.0, 0.58, 28.0, 0.40),
    ]
    animals = []
    for aid, ww, wwa, ced, ceda, stay, staya in rows:
        animals.append(
            Animal(
                animal_id=aid,
                breed="Angus",
                evaluation_id="AAA-2026",
                epds={
                    "WW": EpdValue("WW", ww, wwa),
                    "CED": EpdValue("CED", ced, ceda),
                    "STAY": EpdValue("STAY", stay, staya),
                },
            )
        )
    return AnimalSet(animals=animals, name="Test sale")
