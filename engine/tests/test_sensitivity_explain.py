"""
Tests for tornado sensitivity analysis and plain-language explanations.
"""

import pytest

from osit_index.index import build_index
from osit_index.sensitivity import tornado_sensitivity
from osit_index.explain import explain_score


# --- sensitivity -----------------------------------------------------------
def test_sensitivity_runs_and_orders(maternal_goal, params, angus_animals):
    """Tornado sensitivity returns one entry per goal trait, most-disruptive
    first, with a non-empty plain-language summary."""
    res = tornado_sensitivity(maternal_goal, params, angus_animals)
    assert len(res.entries) == len(maternal_goal.components)
    disruptions = [e.max_disruption for e in res.entries]
    assert disruptions == sorted(disruptions, reverse=True)
    assert res.summary


def test_sensitivity_baseline_top_matches_build(maternal_goal, params,
                                                angus_animals):
    """The sensitivity baseline top animal matches a direct build_index."""
    direct = build_index(maternal_goal, params, angus_animals)
    res = tornado_sensitivity(maternal_goal, params, angus_animals)
    assert res.baseline_top == direct.scores[0].animal_id


def test_rank_correlation_identical_is_one(maternal_goal, params,
                                           angus_animals):
    """A tiny variation should leave rank correlation at or very near 1."""
    res = tornado_sensitivity(maternal_goal, params, angus_animals,
                              variation=0.001)
    for e in res.entries:
        assert e.rank_corr_low == pytest.approx(1.0, abs=1e-9)
        assert e.rank_corr_high == pytest.approx(1.0, abs=1e-9)


# --- explanations ----------------------------------------------------------
def test_explanation_mentions_id_and_rank(maternal_goal, params,
                                          angus_animals):
    """Every animal's explanation names the animal and states its place."""
    result = build_index(maternal_goal, params, angus_animals)
    for score in result.scores:
        text = explain_score(score, result)
        assert score.animal_id in text
        assert "of" in text  # "ranks Nth of M"


def test_explanation_top_animal_is_positive(maternal_goal, params,
                                            angus_animals):
    """The top animal's explanation reads as a strength, not a weakness."""
    result = build_index(maternal_goal, params, angus_animals)
    top_text = explain_score(result.scores[0], result).lower()
    assert "1st of" in top_text
    assert "carried mainly by" in top_text or "helped by" in top_text


def test_explanation_flags_partial(maternal_goal, params, angus_animals):
    """A partial-data animal's explanation says the position is approximate."""
    from osit_index.index import MissingEpdPolicy

    angus_animals.animals[0].epds.pop("STAY")
    result = build_index(maternal_goal, params, angus_animals,
                         missing_policy=MissingEpdPolicy.IMPUTE_MEAN)
    score = next(s for s in result.scores if s.animal_id == "AAA-1842")
    assert "approximate" in explain_score(score, result).lower()
