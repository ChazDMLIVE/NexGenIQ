"""
Tests for the guided economic-value estimator (osit_index.econ_estimator).

These verify that every trait recipe runs, that defaults yield a number,
that user answers move the estimate, and that the economic signs are
correct (a cost trait is negative, a revenue trait positive).
"""

import pytest

from osit_index import (
    available_recipes,
    estimate_economic_value,
    get_recipe,
)


def test_every_recipe_runs_with_defaults():
    """Each recipe yields a finite economic value from its defaults."""
    for code in available_recipes():
        result = estimate_economic_value(code)
        assert isinstance(result.economic_value, float)
        assert abs(result.economic_value) < 1e7
        assert result.formula_text  # the formula is always reported


def test_unknown_trait_rejected():
    """Asking for a trait with no recipe raises a helpful KeyError."""
    with pytest.raises(KeyError):
        estimate_economic_value("NOT_A_TRAIT")


def test_revenue_traits_are_positive():
    """Weaning weight and marbling are revenue traits - positive value."""
    assert estimate_economic_value("WW").economic_value > 0
    assert estimate_economic_value("MARB").economic_value > 0
    assert estimate_economic_value("CED").economic_value > 0
    assert estimate_economic_value("STAY").economic_value > 0


def test_cost_traits_are_negative():
    """Mature weight, backfat and dry-matter intake are cost traits."""
    assert estimate_economic_value("MW").economic_value < 0
    assert estimate_economic_value("FAT").economic_value < 0
    assert estimate_economic_value("DMI").economic_value < 0


def test_answers_change_the_estimate():
    """A higher sale price yields a higher weaning-weight value."""
    low = estimate_economic_value("WW", {"price_per_lb": 1.50})
    high = estimate_economic_value("WW", {"price_per_lb": 3.00})
    assert high.economic_value > low.economic_value


def test_pap_inert_at_low_altitude():
    """With zero altitude death risk, PAP carries ~no economic value."""
    result = estimate_economic_value("PAP", {"death_risk_per_mmHg": 0.0})
    assert abs(result.economic_value) < 1e-6


def test_pap_costly_at_high_altitude():
    """With a real altitude death risk, PAP is a clear cost (negative)."""
    result = estimate_economic_value(
        "PAP",
        {"death_risk_per_mmHg": 0.012, "cost_per_death": 1500.0,
         "fraction_at_altitude": 1.0},
    )
    assert result.economic_value < 0


def test_latent_pap_value_is_scaled_from_raw():
    """The latent-z PAP value is the raw per-mmHg value rescaled through
    the logit slope, so it is larger in magnitude per unit (a latent-z
    unit spans far more biological range than 1 mmHg)."""
    raw = estimate_economic_value(
        "PAP",
        {"death_risk_per_mmHg": 0.012, "cost_per_death": 1500.0},
    )
    latent = estimate_economic_value(
        "PAP_L",
        {"death_risk_per_mmHg": 0.012, "cost_per_death": 1500.0,
         "typical_pap": 41.0},
    )
    # Both are costs.
    assert raw.economic_value < 0
    assert latent.economic_value < 0
    # The latent-z value is larger in magnitude per unit.
    assert abs(latent.economic_value) > abs(raw.economic_value)


def test_answers_clamped_to_range():
    """An out-of-range answer is clamped to the question's bounds."""
    recipe = get_recipe("WW")
    q = next(q for q in recipe.questions if q.key == "fraction_marketed")
    # Ask for a fraction above 1.0; it must be clamped to the maximum.
    result = estimate_economic_value("WW", {"fraction_marketed": 5.0})
    assert result.inputs_used["fraction_marketed"] == q.maximum
