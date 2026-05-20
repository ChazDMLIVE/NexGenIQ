"""
Tests for the versioned reference-data loader.

These verify that the shipped official data files load correctly, that the
loader validates malformed input, and that the loaded USMARC factors match
the published USDA values exactly.
"""

import json

import pytest

from osit_index.dataloader import (
    DataFileError,
    available_data_files,
    load_adjustment_table,
    load_parameter_set,
)


# --- the shipped official data --------------------------------------------
def test_usmarc_table_loads():
    """The shipped USMARC across-breed factor table loads."""
    table, source = load_adjustment_table()
    assert table.version == "USMARC-2026"
    assert table.base_breed == "Angus"
    assert "USMARC" in source.detail.get("publisher", "")


def test_usmarc_factors_match_published_values():
    """Spot-check loaded factors against the published USDA Table 1.

    These are exact values from the official 2026 USDA/USMARC fact sheet.
    """
    table, _ = load_adjustment_table()
    # Angus is the base breed - every factor zero.
    assert table.factor("Angus", "WW") == 0.0
    # Published Hereford factors (January 2026 USMARC Table 1).
    assert table.factor("Hereford", "BW") == pytest.approx(0.8)
    assert table.factor("Hereford", "WW") == pytest.approx(-14.3)
    assert table.factor("Hereford", "CW") == pytest.approx(-68.2)
    # Published Simmental and Charolais factors.
    assert table.factor("Simmental", "BW") == pytest.approx(2.2)
    assert table.factor("Charolais", "REA") == pytest.approx(0.76)
    # Red Angus yearling weight.
    assert table.factor("Red Angus", "YW") == pytest.approx(-21.2)


def test_usmarc_table_covers_eighteen_breeds():
    """The table covers all eighteen breeds USMARC evaluates."""
    table, _ = load_adjustment_table()
    assert len(table.covered_breeds()) == 18


def test_usmarc_carcass_traits_absent_for_some_breeds():
    """Some breeds have no carcass-trait factors (no qualifying USMARC
    carcass data) - the loader represents this as a missing factor, not a
    zero."""
    table, _ = load_adjustment_table()
    # Beefmaster has growth factors but no carcass-weight factor.
    assert table.factor("Beefmaster", "WW") is not None
    assert table.factor("Beefmaster", "CW") is None


def test_consensus_parameters_load():
    """The shipped consensus genetic-parameter set loads and is cited."""
    param_set, source = load_parameter_set()
    assert param_set.version == "consensus-2026.1"
    assert len(param_set.trait_params) >= 15
    assert source.detail.get("primary_sources")
    # Every trait carries a citation.
    assert all(tp.citation for tp in param_set.trait_params.values())


def test_available_data_files_lists_shipped_data():
    """The discovery helper finds the shipped data files."""
    files = available_data_files()
    assert any("across_breed" in f for f in files["adjustment_tables"])
    assert any("genetic" in f for f in files["parameter_sets"])


# --- validation of malformed data -----------------------------------------
def test_missing_file_raises(tmp_path):
    """Loading a non-existent file raises a clear DataFileError."""
    with pytest.raises(DataFileError, match="not found"):
        load_adjustment_table(tmp_path / "nope.json")


def test_bad_schema_rejected(tmp_path):
    """A file with the wrong schema tag is rejected."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": "wrong", "version": "x",
                               "factors": {"Angus": {}}}))
    with pytest.raises(DataFileError, match="schema"):
        load_adjustment_table(bad)


def test_out_of_range_correlation_rejected(tmp_path):
    """A genetic correlation outside [-1, 1] is rejected."""
    bad = tmp_path / "bad_params.json"
    bad.write_text(json.dumps({
        "schema": "nexgeniq.genetic_parameter_set.v1",
        "name": "bad", "version": "x",
        "traits": {"WW": {"heritability": 0.25, "genetic_sd": 22.0}},
        "genetic_correlations": [["WW", "YW", 1.5]],
    }))
    with pytest.raises(DataFileError, match="range"):
        load_parameter_set(bad)


def test_invalid_heritability_rejected(tmp_path):
    """A heritability outside (0, 1] is rejected."""
    bad = tmp_path / "bad_h2.json"
    bad.write_text(json.dumps({
        "schema": "nexgeniq.genetic_parameter_set.v1",
        "name": "bad", "version": "x",
        "traits": {"WW": {"heritability": 1.8, "genetic_sd": 22.0}},
    }))
    with pytest.raises(DataFileError):
        load_parameter_set(bad)


def test_both_usmarc_versions_available():
    """Both the 2024 and 2026 USMARC tables ship and load, so a run made
    against an older version stays reproducible (Phase 2 gap G10)."""
    from pathlib import Path

    data_dir = Path(__file__).parent.parent / "osit_index" / "data"

    table_2026, _ = load_adjustment_table(
        data_dir / "across_breed_factors_2026.json"
    )
    assert table_2026.version == "USMARC-2026"
    assert table_2026.factor("Hereford", "WW") == pytest.approx(-14.3)

    table_2024, _ = load_adjustment_table(
        data_dir / "across_breed_factors_2024.json"
    )
    assert table_2024.version == "USMARC-2024"
    assert table_2024.factor("Hereford", "WW") == pytest.approx(-11.9)

    # The two releases genuinely differ - the update changed the numbers.
    assert table_2026.factor("Hereford", "WW") != (
        table_2024.factor("Hereford", "WW")
    )


def test_default_table_is_current_version():
    """The default across-breed table is the current (2026) release."""
    table, _ = load_adjustment_table()
    assert table.version == "USMARC-2026"
