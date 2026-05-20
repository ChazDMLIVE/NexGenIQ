"""
Tests for marginal economic value (MEV) derivation.

These verify that MEVs are derived, are reproducible, carry sensible signs
(the economic-sanity checks of Phase 3 Part 3B Section 2.5.3), and produce
output in the shape the osit-index engine consumes.
"""

import pytest

from osit_sim import derive_mevs


def test_mevs_derived(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """MEV derivation returns one MEV per simulated trait."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    assert len(result.mevs) == len(genetics)
    assert result.replicates == fast_controls.replicates
    # Every MEV carries a Monte-Carlo standard error.
    assert all(m.mc_std_error >= 0 for m in result.mevs)


def test_mevs_ordered_by_importance(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """MEVs come back ordered most- to least-important by |MEV|."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    mags = [abs(m.mev) for m in result.mevs]
    assert mags == sorted(mags, reverse=True)


def test_mev_derivation_reproducible(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The same controls/seed give the same MEVs (common random numbers)."""
    a = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    b = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    a_map = {m.trait_code: m.mev for m in a.mevs}
    b_map = {m.trait_code: m.mev for m in b.mevs}
    for code in a_map:
        assert a_map[code] == pytest.approx(b_map[code])


def test_weaning_weight_has_positive_value(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """Economic-sanity check: at a weaning sale, heavier calves are worth
    more, so weaning weight must carry a positive economic value."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW"],
    )
    ww = next(m for m in result.mevs if m.trait_code == "WW")
    assert ww.mev > 0


def test_subset_of_traits(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """Deriving MEVs for a chosen subset returns only those traits."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW", "MILK", "STAY"],
    )
    assert {m.trait_code for m in result.mevs} == {"WW", "MILK", "STAY"}


def test_as_economic_weights_shape(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The MEV result converts to the trait->weight mapping the index
    engine's breeding goal expects — the integration seam."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW", "CED"],
    )
    weights = result.as_economic_weights()
    assert set(weights) == {"WW", "CED"}
    assert all(isinstance(v, float) for v in weights.values())


def test_baseline_profit_reported(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The MEV result reports a finite baseline herd profit."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW"],
    )
    assert abs(result.baseline_profit) < 1e9


# --- economic-sign sanity checks (Phase 3 Part 3B Section 2.5.3) -----------
# These guard the economic-logic bugs that the earlier unit tests missed:
# every derived MEV must have the sign breeding economics predicts.

def test_mature_weight_has_negative_value(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """In a cow-calf system mature cow weight must carry a NEGATIVE economic
    value: a bigger cow costs proportionally more to maintain every year,
    which outweighs her modest extra cull value."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["MW"],
    )
    mw = next(m for m in result.mevs if m.trait_code == "MW")
    assert mw.mev < 0


def test_fertility_traits_have_positive_value(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """Calving ease, heifer pregnancy and stayability must all carry
    POSITIVE economic value: better fertility and longevity raise herd
    profit (more calves, fewer costly replacements)."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["CED", "HP", "STAY"],
    )
    by_code = {m.trait_code: m.mev for m in result.mevs}
    assert by_code["CED"] > 0, "calving ease should be positively valued"
    assert by_code["HP"] > 0, "heifer pregnancy should be positively valued"
    assert by_code["STAY"] > 0, "stayability should be positively valued"


def test_weaning_weight_value_is_realistic(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The weaning-weight MEV should be a sensible per-pound figure - of
    order a dollar or two, not hundreds. This guards the per-cow, per-year
    normalisation of the MEV (a missing normalisation inflates it by
    roughly herd-size x horizon)."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW"],
    )
    ww = next(m for m in result.mevs if m.trait_code == "WW")
    assert 0.0 < ww.mev < 10.0
