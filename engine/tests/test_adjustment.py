"""
Tests for multi-breed across-breed adjustment.

Verify that adjustment is applied, is exactly reversible, is skipped when not
needed, and that the engine refuses (with an ERROR) to build a multi-breed
index when a factor is missing — never silently producing a wrong ranking.
"""

import pytest

from osit_index import Animal, AnimalSet, example_adjustment_table
from osit_index.animal import EpdValue
from osit_index.adjustment import apply_across_breed_adjustment
from osit_index.index import build_index
from osit_index import BreedingGoal, EconomicBasis, GoalComponent


def _multibreed_set():
    """Two Angus + two Hereford + one Simmental, all with WW/CED EPDs."""
    rows = [
        ("A-1", "Angus", 70.0, 110.0),
        ("A-2", "Angus", 55.0, 90.0),
        ("H-1", "Hereford", 65.0, 95.0),
        ("H-2", "Hereford", 50.0, 80.0),
        ("S-1", "Simmental", 80.0, 120.0),
    ]
    animals = []
    for aid, breed, ww, yw in rows:
        animals.append(Animal(aid, breed,
                              epds={"WW": EpdValue("WW", ww, 0.7),
                                    "YW": EpdValue("YW", yw, 0.6)},
                              evaluation_id=f"{breed}-2026"))
    return AnimalSet(animals)


def test_single_breed_not_adjusted(angus_animals):
    """A single-breed set is returned unchanged (nothing to adjust)."""
    res = apply_across_breed_adjustment(
        angus_animals, ["WW", "CED", "STAY"], example_adjustment_table()
    )
    assert res.applied is False
    assert res.animal_set is angus_animals


def test_multibreed_adjustment_applied():
    """Hereford EPDs are shifted by the table's Hereford factors."""
    aset = _multibreed_set()
    table = example_adjustment_table()
    res = apply_across_breed_adjustment(aset, ["WW", "YW"], table)
    assert res.applied is True
    assert res.table_version == table.version
    h1 = next(a for a in res.animal_set if a.animal_id == "H-1")
    # Official USMARC January 2026 Hereford weaning-weight factor is -14.3.
    assert h1.epd("WW").value == pytest.approx(65.0 + (-14.3))
    a1 = next(a for a in res.animal_set if a.animal_id == "A-1")
    assert a1.epd("WW").value == pytest.approx(70.0)


def test_adjustment_does_not_mutate_input():
    """Adjustment is a pure transformation; the input set is untouched."""
    aset = _multibreed_set()
    original_h1_ww = aset.animals[2].epd("WW").value
    apply_across_breed_adjustment(aset, ["WW", "YW"],
                                  example_adjustment_table())
    assert aset.animals[2].epd("WW").value == original_h1_ww


def test_adjustment_is_reversible():
    """Subtracting the factor recovers the original within-breed EPD."""
    aset = _multibreed_set()
    table = example_adjustment_table()
    res = apply_across_breed_adjustment(aset, ["WW", "YW"], table)
    for rec in res.records:
        assert rec.adjusted_value - rec.factor == pytest.approx(
            rec.original_value
        )


def test_native_multibreed_skips_adjustment():
    """A declared native multi-breed evaluation is not adjusted."""
    aset = _multibreed_set()
    res = apply_across_breed_adjustment(
        aset, ["WW", "YW"], example_adjustment_table(),
        native_multi_breed=True,
    )
    assert res.applied is False


def test_missing_factor_raises():
    """A multi-breed trait with no published factor raises ValueError."""
    aset = _multibreed_set()
    for a in aset:
        a.epds["STAY"] = EpdValue("STAY", 15.0, 0.5)
    table = example_adjustment_table()
    with pytest.raises(ValueError, match="STAY"):
        apply_across_breed_adjustment(aset, ["WW", "STAY"], table)


def test_multibreed_missing_factor_blocks_build(params):
    """build_index turns a missing-factor situation into an ERROR result."""
    aset = _multibreed_set()
    goal = BreedingGoal(
        "multi", EconomicBasis.PER_COW_EXPOSED,
        [GoalComponent("WW", 1.0), GoalComponent("STAY", 5.0)],
    )
    for a in aset:
        a.epds["STAY"] = EpdValue("STAY", 15.0, 0.5)
    result = build_index(goal, params, aset,
                         adjustment_table=example_adjustment_table())
    assert not result.validation.ok
    assert any(i.code == "adjustment_unavailable"
               for i in result.validation.errors)


def test_multibreed_index_builds_with_factors(params):
    """A multi-breed index builds cleanly when every factor is available."""
    aset = _multibreed_set()
    goal = BreedingGoal(
        "multi", EconomicBasis.PER_COW_EXPOSED,
        [GoalComponent("WW", 1.0), GoalComponent("YW", 0.6)],
    )
    result = build_index(goal, params, aset,
                         adjustment_table=example_adjustment_table())
    assert result.validation.ok
    assert len(result.scores) == 5
    assert result.adjustment_table_version == \
        example_adjustment_table().version
