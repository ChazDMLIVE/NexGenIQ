"""
Tests for BIF accuracy-scale conversions.

These verify the conversions against the worked table in NexGenIQ Phase 1
Section 1.4.1. Getting these wrong silently corrupts every confidence
interval, so they are tested explicitly against known values.
"""

import math

import pytest

from osit_index.parameters import (
    bif_accuracy_to_reliability,
    bif_accuracy_to_theoretical,
    reliability_to_bif_accuracy,
)


# Reference values from the Phase 1 Section 1.4.1 conversion table:
# (BIF accuracy, theoretical r, reliability r^2)
_TABLE = [
    (0.05, 0.31225, 0.097500),
    (0.25, 0.66144, 0.437500),
    (0.50, 0.86603, 0.750000),
    (0.75, 0.96825, 0.937500),
    (0.90, 0.99499, 0.990000),
]


@pytest.mark.parametrize("bif, r, rel", _TABLE)
def test_conversion_table(bif, r, rel):
    """Conversions reproduce the Phase 1 reference table."""
    assert bif_accuracy_to_reliability(bif) == pytest.approx(rel, abs=1e-6)
    assert bif_accuracy_to_theoretical(bif) == pytest.approx(r, abs=1e-5)


@pytest.mark.parametrize("bif", [0.0, 0.1, 0.37, 0.5, 0.83, 0.99, 1.0])
def test_reliability_round_trip(bif):
    """BIF -> reliability -> BIF returns the original value."""
    rel = bif_accuracy_to_reliability(bif)
    assert reliability_to_bif_accuracy(rel) == pytest.approx(bif, abs=1e-12)


def test_known_identity_half():
    """The documented landmark: BIF 0.50 == reliability 0.75 exactly."""
    assert bif_accuracy_to_reliability(0.50) == pytest.approx(0.75)


def test_bif_is_lower_than_theoretical_accuracy():
    """BIF accuracy is always <= theoretical accuracy for 0 < acc < 1."""
    for bif in [0.1, 0.3, 0.5, 0.7, 0.9]:
        assert bif <= bif_accuracy_to_theoretical(bif) + 1e-12


def test_zero_and_one_are_fixed_points():
    """0 and 1 map to themselves on every scale."""
    assert bif_accuracy_to_reliability(0.0) == 0.0
    assert bif_accuracy_to_reliability(1.0) == 1.0
    assert bif_accuracy_to_theoretical(1.0) == pytest.approx(1.0)


def test_out_of_range_rejected():
    """Out-of-range inputs raise ValueError."""
    with pytest.raises(ValueError):
        bif_accuracy_to_reliability(-0.1)
    with pytest.raises(ValueError):
        bif_accuracy_to_reliability(1.5)
    with pytest.raises(ValueError):
        reliability_to_bif_accuracy(2.0)


def test_definition_formula():
    """The conversion matches the BIF definition 1 - sqrt(1 - rel) directly."""
    for bif in [0.2, 0.55, 0.88]:
        rel = bif_accuracy_to_reliability(bif)
        assert 1.0 - math.sqrt(1.0 - rel) == pytest.approx(bif)
