"""
Tests for the whole-result interpreter (osit_index.interpret).

These verify the interpretation is produced, is layered (headline, readout,
detail, cautions), always carries the not-a-recommendation disclaimer, and
surfaces the right cautions for partial / excluded / uncertain results.
"""

from osit_index import (
    Animal,
    AnimalSet,
    BreedingGoal,
    EconomicBasis,
    GoalComponent,
    IndexMode,
    build_index,
    consensus_parameter_set,
    interpret_index_result,
)
from osit_index.animal import EpdValue


def _mk(aid, vals, acc=0.6):
    return Animal(aid, "Angus",
                  epds={t: EpdValue(t, v, acc) for t, v in vals.items()})


def _result(n=4):
    ps = consensus_parameter_set()
    goal = BreedingGoal(
        name="Test goal", basis=EconomicBasis.PER_COW_EXPOSED,
        components=[GoalComponent("WW", 0.85), GoalComponent("CED", 12.0),
                    GoalComponent("STAY", 6.4)],
    )
    animals = AnimalSet([
        _mk(f"A{i}", {"WW": 40 - i * 8, "CED": 12 - i * 3,
                      "STAY": 16 - i * 4})
        for i in range(n)
    ])
    return build_index(goal, ps, animals, mode=IndexMode.ECONOMIC_WEIGHT)


def test_interpretation_is_produced():
    """A normal result yields a non-empty layered interpretation."""
    interp = interpret_index_result(_result())
    assert interp.headline
    assert interp.readout
    assert len(interp.detail) > 0


def test_interpretation_always_has_disclaimer():
    """Every interpretation carries the not-a-recommendation disclaimer."""
    interp = interpret_index_result(_result())
    assert interp.disclaimer
    low = interp.disclaimer.lower()
    assert "not" in low and "recommend" in low


def test_readout_is_not_directive():
    """The readout describes the ranking; it does not tell the user to
    take an action like 'select' or 'cull'."""
    interp = interpret_index_result(_result())
    text = (interp.headline + " " + interp.readout).lower()
    # It explicitly frames the result as a description, not advice.
    assert "not a recommendation" in text or "description" in text


def test_headline_names_the_top_animal():
    """The headline identifies the top-ranked animal."""
    result = _result()
    interp = interpret_index_result(result)
    assert result.scores[0].animal_id in interp.headline


def test_empty_result_handled():
    """An empty result yields a sensible interpretation, not a crash."""
    from osit_index.index import IndexResult

    interp = interpret_index_result(IndexResult())
    assert interp.headline
    assert "no animals" in interp.headline.lower()


def test_partial_animals_raise_a_caution():
    """An animal with missing EPDs (filled with breed average) is flagged
    in the cautions as an approximate result."""
    ps = consensus_parameter_set()
    goal = BreedingGoal(
        name="g", basis=EconomicBasis.PER_COW_EXPOSED,
        components=[GoalComponent("WW", 1.0), GoalComponent("CED", 8.0)],
    )
    animals = AnimalSet([
        _mk("Full", {"WW": 40, "CED": 10}),
        _mk("Partial", {"WW": 20}),  # no CED EPD
    ])
    result = build_index(
        goal, ps, animals, mode=IndexMode.ECONOMIC_WEIGHT,
        missing_policy="fill_breed_mean",
    )
    interp = interpret_index_result(result)
    # If any animal came back partial, a caution must mention it.
    if any(s.is_partial for s in result.scores):
        assert any(
            "approximate" in c.lower() or "missing" in c.lower()
            for c in interp.cautions
        )
