"""
Tests for the osit-sim herd simulation.

These verify the simulation runs, is reproducible, behaves sensibly as
inputs change, and that the input models validate their arguments.
"""

import pytest

from osit_sim import (
    BreedComposition,
    ProductionSystem,
    SimulationControls,
    run_simulation,
)


def test_simulation_runs(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """A simulation completes and returns a populated result."""
    result = run_simulation(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    assert result.calves_weaned_per_year > 0
    assert result.mean_cow_age > 0
    # A real cow-calf operation can run a loss or a profit; we only assert
    # the figure is finite and sane in magnitude.
    assert abs(result.net_present_profit) < 1e9


def test_simulation_is_reproducible(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The same seed produces exactly the same result."""
    a = run_simulation(
        maternal_system, weaning_economics, fast_controls, genetics,
        seed=12345,
    )
    b = run_simulation(
        maternal_system, weaning_economics, fast_controls, genetics,
        seed=12345,
    )
    assert a.net_present_profit == b.net_present_profit
    assert a.calves_weaned_per_year == b.calves_weaned_per_year


def test_different_seeds_differ(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """Different seeds give different (stochastic) results."""
    a = run_simulation(
        maternal_system, weaning_economics, fast_controls, genetics,
        seed=1,
    )
    b = run_simulation(
        maternal_system, weaning_economics, fast_controls, genetics,
        seed=2,
    )
    assert a.net_present_profit != b.net_present_profit


def test_age_distribution_converges(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """After burn-in the mean cow age is in a biologically sensible band."""
    result = run_simulation(
        maternal_system, weaning_economics, fast_controls, genetics
    )
    assert result.converged
    assert 2.0 <= result.mean_cow_age <= 11.0


def test_terminal_system_runs(
    terminal_system, weaning_economics, fast_controls, genetics
):
    """A terminal system (no retained heifers) simulates without error."""
    result = run_simulation(
        terminal_system, weaning_economics, fast_controls, genetics
    )
    assert result.calves_weaned_per_year > 0


def test_higher_conception_weans_more(
    weaning_economics, fast_controls, genetics
):
    """A herd with higher conception weans more calves — a sanity check."""
    low = ProductionSystem(
        name="low", herd_size=150, conception_rate=0.70,
        cow_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
    )
    high = ProductionSystem(
        name="high", herd_size=150, conception_rate=0.95,
        cow_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
    )
    low_r = run_simulation(
        low, weaning_economics, fast_controls, genetics, seed=7
    )
    high_r = run_simulation(
        high, weaning_economics, fast_controls, genetics, seed=7
    )
    assert (
        high_r.calves_weaned_per_year > low_r.calves_weaned_per_year
    )


def test_herd_size_scales_weaned(
    weaning_economics, fast_controls, genetics
):
    """A bigger herd weans more calves, roughly in proportion."""
    small = ProductionSystem(
        name="small", herd_size=80,
        cow_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
    )
    big = ProductionSystem(
        name="big", herd_size=320,
        cow_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
        bull_breed_composition=[BreedComposition(1.0, {"Angus": 1.0})],
    )
    s = run_simulation(
        small, weaning_economics, fast_controls, genetics, seed=3
    )
    b = run_simulation(
        big, weaning_economics, fast_controls, genetics, seed=3
    )
    assert b.calves_weaned_per_year > 3 * s.calves_weaned_per_year


# --- input validation ------------------------------------------------------
def test_bad_breed_composition_rejected():
    """Breed-composition fractions that do not sum to 1 are rejected."""
    with pytest.raises(ValueError, match="sum to 1"):
        ProductionSystem(
            name="bad",
            cow_breed_composition=[
                BreedComposition(0.4, {"Angus": 1.0}),
                BreedComposition(0.4, {"Hereford": 1.0}),
            ],
        )


def test_bad_rate_rejected():
    """An out-of-range probability is rejected."""
    with pytest.raises(ValueError):
        ProductionSystem(name="bad", conception_rate=1.5)


def test_bad_controls_rejected():
    """Invalid simulation controls are rejected."""
    with pytest.raises(ValueError):
        SimulationControls(planning_horizon_years=0)
    with pytest.raises(ValueError):
        SimulationControls(replicates=0)
