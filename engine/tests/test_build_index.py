"""
Integration tests for build_index — the top-level engine entry point.

These verify the end-to-end pipeline: scoring, ranking, contributions,
uncertainty, and the economic-weight index against a hand-worked result.
"""

import pytest

from osit_index.index import IndexMode, MissingEpdPolicy, build_index


def test_economic_weight_index_handworked(maternal_goal, params,
                                          angus_animals):
    """The economic-weight index value matches a hand calculation.

    In ECONOMIC_WEIGHT mode b == a, so the index value of an animal is
    simply sum(economic_weight * EPD). For AAA-1842:
        WW   72.0 * 0.85 = 61.20
        CED  14.0 * 12.0 = 168.00
        STAY 22.0 * 6.4  = 140.80
        total            = 370.00
    """
    result = build_index(maternal_goal, params, angus_animals,
                         mode=IndexMode.ECONOMIC_WEIGHT)
    assert result.validation.ok
    top = next(s for s in result.scores if s.animal_id == "AAA-1842")
    assert top.index_value == pytest.approx(370.00, abs=1e-9)


def test_contributions_sum_to_index_value(maternal_goal, params,
                                          angus_animals):
    """Per-trait contributions always sum to the animal's index value."""
    result = build_index(maternal_goal, params, angus_animals)
    for score in result.scores:
        assert sum(score.contributions.values()) == pytest.approx(
            score.index_value, abs=1e-9
        )


def test_ranking_is_descending(maternal_goal, params, angus_animals):
    """Animals are returned best-first, with consecutive ranks."""
    result = build_index(maternal_goal, params, angus_animals)
    values = [s.index_value for s in result.scores]
    assert values == sorted(values, reverse=True)
    assert [s.rank for s in result.scores] == list(
        range(1, len(result.scores) + 1)
    )


def test_weights_equal_economic_weights_in_economic_mode(
    maternal_goal, params, angus_animals
):
    """In ECONOMIC_WEIGHT mode the index weights equal the economic weights."""
    result = build_index(maternal_goal, params, angus_animals,
                         mode=IndexMode.ECONOMIC_WEIGHT)
    for comp in maternal_goal.components:
        assert result.weights[comp.trait_code] == pytest.approx(
            comp.economic_weight
        )


def test_confidence_interval_present_and_ordered(maternal_goal, params,
                                                 angus_animals):
    """Every animal with accuracies gets an ordered 95% CI around its value."""
    result = build_index(maternal_goal, params, angus_animals)
    for score in result.scores:
        assert score.std_error is not None and score.std_error >= 0
        assert score.ci_low < score.index_value < score.ci_high


def test_ordering_invariant_to_input_order(maternal_goal, params,
                                           angus_animals):
    """Shuffling the input animals does not change the resulting ranking."""
    import random

    result_a = build_index(maternal_goal, params, angus_animals)
    shuffled = list(angus_animals.animals)
    random.Random(1).shuffle(shuffled)
    angus_animals.animals = shuffled
    result_b = build_index(maternal_goal, params, angus_animals)

    assert [s.animal_id for s in result_a.scores] == [
        s.animal_id for s in result_b.scores
    ]


def test_missing_epd_exclude_policy(maternal_goal, params, angus_animals):
    """Under EXCLUDE, an animal missing an index trait is dropped + warned."""
    angus_animals.animals[0].epds.pop("STAY")
    result = build_index(maternal_goal, params, angus_animals,
                         missing_policy=MissingEpdPolicy.EXCLUDE)
    assert "AAA-1842" in result.excluded
    assert "AAA-1842" not in [s.animal_id for s in result.scores]
    assert any(i.code == "animal_excluded"
               for i in result.validation.warnings)


def test_missing_epd_impute_policy(maternal_goal, params, angus_animals):
    """Under IMPUTE_MEAN, a missing EPD becomes 0 and the score is partial."""
    angus_animals.animals[0].epds.pop("STAY")
    result = build_index(maternal_goal, params, angus_animals,
                         missing_policy=MissingEpdPolicy.IMPUTE_MEAN)
    score = next(s for s in result.scores if s.animal_id == "AAA-1842")
    assert score.is_partial
    # STAY imputed to 0 -> contributes 0.
    assert score.contributions["STAY"] == pytest.approx(0.0)


def test_empty_goal_blocks_run(params, angus_animals):
    """A goal with no traits produces an ERROR and no scores."""
    from osit_index import BreedingGoal, EconomicBasis

    empty = BreedingGoal("empty", EconomicBasis.PER_COW_EXPOSED, [])
    result = build_index(empty, params, angus_animals)
    assert not result.validation.ok
    assert result.scores == []
    assert any(i.code == "empty_goal" for i in result.validation.errors)
