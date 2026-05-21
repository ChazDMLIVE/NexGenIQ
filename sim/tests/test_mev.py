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
    """MEV derivation returns one MEV per breed-available trait."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    # A single-breed Angus herd publishes every trait including PAP.
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
    maternal_system, weaning_economics, sign_controls, genetics
):
    """In a cow-calf system mature cow weight must carry a NEGATIVE economic
    value: a bigger cow costs proportionally more to maintain every year,
    which outweighs her modest extra cull value."""
    result = derive_mevs(
        maternal_system, weaning_economics, sign_controls, genetics,
        traits=["MW"],
    )
    mw = next(m for m in result.mevs if m.trait_code == "MW")
    assert mw.mev < 0


def test_fertility_traits_have_positive_value(
    maternal_system, weaning_economics, sign_controls, genetics
):
    """Calving ease, heifer pregnancy and stayability must all carry
    POSITIVE economic value: better fertility and longevity raise herd
    profit (more calves, fewer costly replacements).

    Uses ``sign_controls`` (more replicates) because stayability's MEV is
    small and estimated from a noisy difference - too few replicates can
    flip its sign by Monte-Carlo chance alone."""
    result = derive_mevs(
        maternal_system, weaning_economics, sign_controls, genetics,
        traits=["CED", "HP", "STAY"],
    )
    by_code = {m.trait_code: m.mev for m in result.mevs}
    assert by_code["CED"] > 0, "calving ease should be positively valued"
    assert by_code["HP"] > 0, "heifer pregnancy should be positively valued"
    assert by_code["STAY"] > 0, "stayability should be positively valued"


def test_birth_weight_has_negative_value(
    maternal_system, weaning_economics, sign_controls, genetics
):
    """Birth weight must carry a NEGATIVE economic value: a heavier calf at
    birth raises dystocia loss, so more BW means fewer calves weaned."""
    result = derive_mevs(
        maternal_system, weaning_economics, sign_controls, genetics,
        traits=["BW"],
    )
    bw = next(m for m in result.mevs if m.trait_code == "BW")
    assert bw.mev < 0


# --- carcass / terminal endpoint checks -----------------------------------
# The point of the expansion: on a carcass grid the carcass traits must
# carry real economic value (they were inert before the engine wired them
# into the grid valuation).

def test_carcass_traits_valued_on_the_grid(
    terminal_system, carcass_economics, sign_controls, genetics
):
    """On a carcass-grid endpoint marbling and ribeye area must carry
    POSITIVE value and backfat NEGATIVE - the grid rewards quality grade
    and red-meat yield and discounts excess trim fat."""
    result = derive_mevs(
        terminal_system, carcass_economics, sign_controls, genetics,
        traits=["MARB", "REA", "FAT"],
    )
    by_code = {m.trait_code: m.mev for m in result.mevs}
    assert by_code["MARB"] > 0, "marbling should be positively valued"
    assert by_code["REA"] > 0, "ribeye area should be positively valued"
    assert by_code["FAT"] < 0, "backfat should be negatively valued"


def test_feed_efficiency_valued_when_fed(
    terminal_system, carcass_economics, sign_controls, genetics
):
    """When calves are fed to a carcass endpoint, residual feed intake
    must carry a NEGATIVE economic value: a higher (worse) RFI means more
    feed bought for the same gain."""
    result = derive_mevs(
        terminal_system, carcass_economics, sign_controls, genetics,
        traits=["RFI"],
    )
    rfi = next(m for m in result.mevs if m.trait_code == "RFI")
    assert rfi.mev < 0


# --- PAP / altitude checks ------------------------------------------------

def test_pap_excluded_for_non_publishing_breed(
    weaning_economics, sign_controls, genetics
):
    """PAP is published only by Angus, Red Angus and Simmental. A herd of
    a breed that does not evaluate PAP (Charolais) must not get a PAP MEV
    in the default trait set."""
    from osit_sim import BreedComposition, ProductionSystem

    charolais = ProductionSystem(
        name="Charolais herd",
        herd_size=120,
        cow_breed_composition=[BreedComposition(1.0, {"Charolais": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Charolais": 1.0})],
    )
    result = derive_mevs(
        charolais, weaning_economics, sign_controls, genetics
    )
    assert "PAP" not in {m.trait_code for m in result.mevs}


def test_pap_makes_no_difference_at_low_altitude(
    maternal_system, weaning_economics, genetics
):
    """At low elevation, high-altitude disease causes no loss, so a herd
    with a high-PAP genetic shift must be no less profitable than one with
    a low-PAP shift. Tested directly on simulated profit (averaged over
    many herds) rather than on the noisy finite-difference MEV, because
    PAP acts through rare stochastic deaths.

    This is the mechanism check behind PAP's near-zero MEV at low
    elevation; the low-altitude MEV itself is verified separately."""
    from osit_sim import run_simulation

    low = weaning_economics
    low.elevation_ft = 1000.0
    ctrl = _profit_controls()
    seeds = list(range(101, 117))
    hi_pap = _mean_profit(
        maternal_system, low, ctrl, genetics, {"PAP": +8.0}, seeds
    )
    lo_pap = _mean_profit(
        maternal_system, low, ctrl, genetics, {"PAP": -8.0}, seeds
    )
    # No altitude stress -> PAP shift must not move profit appreciably.
    assert abs(hi_pap - lo_pap) < 0.01 * abs(lo_pap)


def test_higher_pap_is_costly_at_high_altitude(
    maternal_system, weaning_economics, genetics
):
    """At high elevation, a herd carrying a high-PAP genetic shift suffers
    more death loss and culling than a low-PAP herd, so it must be LESS
    profitable. Tested directly on mean simulated profit over many herds,
    which resolves the effect cleanly where the finite-difference MEV is
    swamped by Monte-Carlo noise (PAP acts through rare deaths)."""
    from osit_sim import run_simulation

    high = weaning_economics
    high.elevation_ft = 9000.0
    ctrl = _profit_controls()
    seeds = list(range(201, 217))
    hi_pap = _mean_profit(
        maternal_system, high, ctrl, genetics, {"PAP": +8.0}, seeds
    )
    lo_pap = _mean_profit(
        maternal_system, high, ctrl, genetics, {"PAP": -8.0}, seeds
    )
    # Higher PAP at altitude -> more death loss -> lower profit.
    assert hi_pap < lo_pap


def _profit_controls():
    """Controls for a direct profit comparison (single herd per seed)."""
    from osit_sim import SimulationControls

    return SimulationControls(
        burn_in_years=4, planning_horizon_years=8, replicates=1,
        seed=20260520,
    )


def _mean_profit(system, economics, controls, genetics, shift, seeds):
    """Mean net-present profit over several common-random-number seeds."""
    from osit_sim import run_simulation

    total = 0.0
    for s in seeds:
        result = run_simulation(
            system, economics, controls, genetics,
            seed=s, genetic_shift=shift,
        )
        total += result.net_present_profit
    return total / len(seeds)
