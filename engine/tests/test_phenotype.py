"""Tests for the phenotype-to-breeding-value conversion (osit_index.phenotype).

These cover the mass-selection conversion a producer with raw,
age-standardized performance records relies on: within-contemporary-group
adjustment, the EBV = h2 * deviation predictor, the sqrt(h2) accuracy, and
the input guardrails.
"""

import math

import pytest

from osit_index import (
    PhenotypeRecord,
    PhenotypeInputError,
    convert_phenotypes,
    own_performance_accuracy,
)
from osit_index.animal import EpdScale


def test_own_performance_accuracy_is_sqrt_h2():
    """The single-record own-performance accuracy is sqrt(h2)."""
    assert own_performance_accuracy(0.25) == pytest.approx(0.5)
    assert own_performance_accuracy(0.49) == pytest.approx(0.7)


def test_own_performance_accuracy_rejects_bad_h2():
    """Heritability outside (0, 1] is rejected."""
    with pytest.raises(PhenotypeInputError):
        own_performance_accuracy(0.0)
    with pytest.raises(PhenotypeInputError):
        own_performance_accuracy(1.5)


def test_conversion_centres_on_contemporary_group_mean(params):
    """EBV is h2 * (phenotype - contemporary-group mean), on the EBV scale."""
    recs = [
        PhenotypeRecord("A", "g1", "Angus", {"WW": 520.0}),
        PhenotypeRecord("B", "g1", "Angus", {"WW": 560.0}),
        PhenotypeRecord("C", "g1", "Angus", {"WW": 500.0}),
        PhenotypeRecord("D", "g1", "Angus", {"WW": 540.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW"])
    h2 = params.trait_params["WW"].heritability
    by_id = {a.animal_id: a for a in res.animal_set}
    # Group mean is 530; B is +30 above it.
    assert by_id["B"].epd("WW").value == pytest.approx(h2 * 30.0)
    assert by_id["C"].epd("WW").value == pytest.approx(h2 * -30.0)
    # Deviations sum to zero -> EBVs sum to zero.
    total = sum(a.epd("WW").value for a in res.animal_set)
    assert total == pytest.approx(0.0)


def test_conversion_marks_values_as_ebv_with_sqrt_h2_accuracy(params):
    """Converted predictions are EBV-scale and carry sqrt(h2) accuracy."""
    recs = [
        PhenotypeRecord("A", "g1", "Angus", {"WW": 520.0}),
        PhenotypeRecord("B", "g1", "Angus", {"WW": 540.0}),
        PhenotypeRecord("C", "g1", "Angus", {"WW": 560.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW"])
    h2 = params.trait_params["WW"].heritability
    for a in res.animal_set:
        e = a.epd("WW")
        assert e.scale is EpdScale.EBV
        assert e.bif_accuracy == pytest.approx(math.sqrt(h2))


def test_separate_groups_are_adjusted_separately(params):
    """Animals are compared only within their own contemporary group."""
    recs = [
        # Easy group: high absolute weights.
        PhenotypeRecord("A", "easy", "Angus", {"WW": 600.0}),
        PhenotypeRecord("B", "easy", "Angus", {"WW": 620.0}),
        PhenotypeRecord("C", "easy", "Angus", {"WW": 640.0}),
        # Hard group: low absolute weights.
        PhenotypeRecord("D", "hard", "Angus", {"WW": 480.0}),
        PhenotypeRecord("E", "hard", "Angus", {"WW": 500.0}),
        PhenotypeRecord("F", "hard", "Angus", {"WW": 520.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW"])
    by_id = {a.animal_id: a for a in res.animal_set}
    # The top animal in the hard group (F, +20 dev) outranks the bottom
    # animal in the easy group (A, -20 dev) despite a far lower raw weight.
    assert by_id["F"].epd("WW").value > by_id["A"].epd("WW").value


def test_missing_contemporary_group_rejected(params):
    """An animal with no contemporary group is rejected with a clear error."""
    recs = [PhenotypeRecord("A", "", "Angus", {"WW": 540.0})]
    with pytest.raises(PhenotypeInputError, match="contemporary group"):
        convert_phenotypes(recs, params, ["WW"])


def test_no_records_rejected(params):
    """An empty record list is rejected."""
    with pytest.raises(PhenotypeInputError, match="No phenotype records"):
        convert_phenotypes([], params, ["WW"])


def test_trait_with_no_data_is_skipped_with_warning(params):
    """A goal trait with no phenotype column is skipped, not fatal."""
    recs = [
        PhenotypeRecord("A", "g1", "Angus", {"WW": 520.0}),
        PhenotypeRecord("B", "g1", "Angus", {"WW": 560.0}),
        PhenotypeRecord("C", "g1", "Angus", {"WW": 540.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW", "YW"])
    assert any("YW" in w for w in res.warnings)
    # WW still converted.
    assert all(a.epd("WW") is not None for a in res.animal_set)


def test_all_traits_missing_raises(params):
    """If no goal trait has any data, the conversion fails clearly."""
    recs = [PhenotypeRecord("A", "g1", "Angus", {})]
    with pytest.raises(PhenotypeInputError, match="None of"):
        convert_phenotypes(recs, params, ["WW"])


def test_small_contemporary_group_warns(params):
    """A contemporary group too small for a reliable mean triggers a warning."""
    recs = [
        PhenotypeRecord("A", "tiny", "Angus", {"WW": 540.0}),
        PhenotypeRecord("B", "tiny", "Angus", {"WW": 560.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW"])
    assert any("tiny" in w and "small" in w for w in res.warnings)


def test_group_summaries_record_means(params):
    """The conversion records the contemporary-group means it used."""
    recs = [
        PhenotypeRecord("A", "g1", "Angus", {"WW": 500.0}),
        PhenotypeRecord("B", "g1", "Angus", {"WW": 540.0}),
        PhenotypeRecord("C", "g1", "Angus", {"WW": 580.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW"])
    summ = [s for s in res.group_summaries if s.trait_code == "WW"]
    assert len(summ) == 1
    assert summ[0].n == 3
    assert summ[0].mean == pytest.approx(540.0)


def test_evaluation_label_records_phenotype_provenance(params):
    """Converted animals carry an evaluation id marking phenotype origin."""
    recs = [
        PhenotypeRecord("A", "g1", "Angus", {"WW": 520.0}),
        PhenotypeRecord("B", "g1", "Angus", {"WW": 540.0}),
        PhenotypeRecord("C", "g1", "Angus", {"WW": 560.0}),
    ]
    res = convert_phenotypes(recs, params, ["WW"])
    for a in res.animal_set:
        assert "phenotype" in a.evaluation_id.lower()


def test_pap_converts_like_any_trait(params):
    """PAP, a directly measured phenotype, converts the same way as weights."""
    recs = [
        PhenotypeRecord("A", "g1", "Angus", {"PAP": 38.0}),
        PhenotypeRecord("B", "g1", "Angus", {"PAP": 42.0}),
        PhenotypeRecord("C", "g1", "Angus", {"PAP": 46.0}),
    ]
    res = convert_phenotypes(recs, params, ["PAP"])
    h2 = params.trait_params["PAP"].heritability
    by_id = {a.animal_id: a for a in res.animal_set}
    # Group mean 42; A is -4 below it.
    assert by_id["A"].epd("PAP").value == pytest.approx(h2 * -4.0)
