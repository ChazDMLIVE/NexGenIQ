"""
Tests for the validation engine.

These verify that bad input is caught with the correct severity and never
silently produces a result — the non-negotiable correctness requirement for
software that informs real breeding decisions (Phase 3 Part 3A Section 1.4).
"""

import numpy as np
import pytest

from osit_index import BreedingGoal, EconomicBasis, GoalComponent
from osit_index.index import IndexMode, build_index
from osit_index.validation import (
    Severity,
    ValidationReport,
    check_covariance_matrix,
    validate_goal,
)


def test_non_pd_matrix_is_error():
    """A non-positive-definite matrix is flagged ERROR when PD is required."""
    report = ValidationReport()
    bad = np.array([[1.0, 2.0], [2.0, 1.0]])  # eigenvalues 3, -1
    check_covariance_matrix(bad, report, name="P", require_pd=True)
    assert not report.ok
    assert any(i.code == "matrix_not_pd" for i in report.errors)


def test_pd_matrix_passes():
    """A valid positive-definite matrix produces no issues."""
    report = ValidationReport()
    good = np.array([[2.0, 0.5], [0.5, 2.0]])
    check_covariance_matrix(good, report, name="P", require_pd=True)
    assert report.ok


def test_asymmetric_matrix_is_error():
    """An asymmetric matrix is rejected."""
    report = ValidationReport()
    bad = np.array([[1.0, 0.3], [0.9, 1.0]])
    check_covariance_matrix(bad, report, name="G0", require_pd=False)
    assert any(i.code == "matrix_not_symmetric" for i in report.errors)


def test_redundant_traits_warn():
    """A goal with a composite trait and its components warns of double-count."""
    report = ValidationReport()
    goal = BreedingGoal(
        "redundant", EconomicBasis.PER_COW_EXPOSED,
        [GoalComponent("YW", 1.0), GoalComponent("WW", 1.0),
         GoalComponent("PWG", 1.0)],
    )
    validate_goal(goal, report)
    assert any(i.code == "redundant_traits" for i in report.warnings)


def test_single_trait_goal_info():
    """A single-trait goal produces an INFO note, not an error."""
    report = ValidationReport()
    goal = BreedingGoal("solo", EconomicBasis.PER_COW_EXPOSED,
                        [GoalComponent("WW", 1.0)])
    validate_goal(goal, report)
    assert report.ok
    assert any(i.code == "single_trait_goal" for i in report.infos)


def test_low_accuracy_warns(maternal_goal, params, angus_animals):
    """A very-low-accuracy EPD triggers a WARN, not a blocked run."""
    angus_animals.animals[0].epds["WW"].bif_accuracy = 0.02
    result = build_index(maternal_goal, params, angus_animals)
    assert result.validation.ok  # still produces a result
    assert any(i.code == "low_accuracy" for i in result.validation.warnings)


def test_missing_accuracy_warns(maternal_goal, params, angus_animals):
    """An EPD with no accuracy warns that the CI will be unreliable."""
    angus_animals.animals[0].epds["WW"].bif_accuracy = None
    result = build_index(maternal_goal, params, angus_animals)
    assert any(i.code == "missing_accuracy"
               for i in result.validation.warnings)


def test_duplicate_trait_in_goal_rejected():
    """A goal listing a trait twice raises at construction."""
    with pytest.raises(ValueError, match="more than once"):
        BreedingGoal("dupe", EconomicBasis.PER_COW_EXPOSED,
                     [GoalComponent("WW", 1.0), GoalComponent("WW", 2.0)])


def test_report_severity_partitioning():
    """errors / warnings / infos partition the issue list correctly."""
    report = ValidationReport()
    report.add(Severity.ERROR, "e", "err")
    report.add(Severity.WARN, "w", "warn")
    report.add(Severity.INFO, "i", "info")
    assert len(report.errors) == 1
    assert len(report.warnings) == 1
    assert len(report.infos) == 1
    assert not report.ok
