"""
Tests for the PAP / latent-PAP traits, the nearest-PD correlation-matrix
repair, and breed-gating in the index engine.
"""

import numpy as np
import pytest

from osit_index import (
    TRAIT_REGISTRY,
    Animal,
    AnimalSet,
    BreedingGoal,
    EconomicBasis,
    GoalComponent,
    IndexMode,
    Severity,
    build_index,
    consensus_parameter_set,
    is_positive_definite,
    nearest_pd_correlation,
)
from osit_index.animal import EpdValue


# --- PAP traits in the registry and parameter set -------------------------

def test_pap_traits_registered():
    """Both raw PAP and latent-scale PAP are in the trait registry."""
    assert "PAP" in TRAIT_REGISTRY
    assert "PAP_L" in TRAIT_REGISTRY
    # Both are breed-restricted (published by a defined set of breeds).
    assert TRAIT_REGISTRY["PAP"].breeds
    assert TRAIT_REGISTRY["PAP_L"].breeds


def test_pap_traits_in_parameter_set():
    """The consensus parameter set carries heritabilities for both PAP
    traits, and the latent trait's heritability exceeds raw PAP's - the
    central result of the latent-phenotype framework."""
    ps = consensus_parameter_set()
    assert "PAP" in ps.trait_params
    assert "PAP_L" in ps.trait_params
    assert ps.heritability("PAP_L") > ps.heritability("PAP")


# --- nearest-PD correlation-matrix repair ---------------------------------

def test_nearest_pd_leaves_valid_matrix_unchanged():
    """A matrix that is already positive-definite is returned essentially
    unchanged by the repair."""
    valid = np.array([[1.0, 0.3, 0.2],
                      [0.3, 1.0, 0.1],
                      [0.2, 0.1, 1.0]])
    repaired = nearest_pd_correlation(valid)
    assert np.allclose(repaired, valid, atol=1e-6)


def test_nearest_pd_repairs_invalid_matrix():
    """An inconsistent (non-PD) correlation matrix is repaired to a valid,
    well-conditioned positive-definite correlation matrix."""
    # These three pairwise correlations cannot all hold at once.
    bad = np.array([[1.0, 0.9, -0.9],
                    [0.9, 1.0, 0.9],
                    [-0.9, 0.9, 1.0]])
    assert not is_positive_definite(bad)
    repaired = nearest_pd_correlation(bad)
    assert is_positive_definite(repaired)
    # Diagonal is restored to one.
    assert np.allclose(np.diag(repaired), 1.0)
    # The repaired matrix is well-conditioned, not merely barely PD.
    cond = np.linalg.cond(repaired)
    assert cond < 1e4


def test_consensus_set_full_matrix_is_repairable():
    """The shipped consensus parameter set spans many traits whose
    pairwise correlations are not jointly consistent; the engine must
    flag this and produce a valid covariance matrix."""
    ps = consensus_parameter_set()
    codes = list(ps.trait_params)
    # The full set is detected as needing a repair.
    assert ps.correlation_was_repaired(codes)
    # The repaired covariance matrix is a valid (PD) matrix.
    G0 = ps.genetic_covariance_matrix(codes, repair=True)
    assert np.linalg.eigvalsh(G0).min() > 0


# --- breed-gating in validation -------------------------------------------

def _mk(aid, breed, vals):
    return Animal(aid, breed,
                  epds={t: EpdValue(t, v, 0.6) for t, v in vals.items()})


def test_pap_in_goal_for_non_publishing_breed_warns():
    """A goal that includes PAP for a herd of a breed that does not
    publish a PAP EPD raises a breed-restricted-trait warning."""
    ps = consensus_parameter_set()
    goal = BreedingGoal(
        name="PAP for Charolais", basis=EconomicBasis.PER_COW_EXPOSED,
        components=[GoalComponent("WW", 1.0), GoalComponent("PAP", -2.0)],
    )
    animals = AnimalSet([
        _mk("C1", "Charolais", {"WW": 20, "PAP": -1.0}),
        _mk("C2", "Charolais", {"WW": 10, "PAP": 2.0}),
    ])
    res = build_index(goal, ps, animals, mode=IndexMode.ECONOMIC_WEIGHT)
    codes = [i.code for i in res.validation.issues]
    assert "breed_restricted_trait" in codes


def test_pap_in_goal_for_publishing_breed_no_warning():
    """PAP in the goal for an Angus herd does not raise the breed
    warning - Angus publishes a PAP EPD."""
    ps = consensus_parameter_set()
    goal = BreedingGoal(
        name="PAP for Angus", basis=EconomicBasis.PER_COW_EXPOSED,
        components=[GoalComponent("WW", 1.0), GoalComponent("PAP", -2.0)],
    )
    animals = AnimalSet([
        _mk("A1", "Angus", {"WW": 20, "PAP": -1.0}),
        _mk("A2", "Angus", {"WW": 10, "PAP": 2.0}),
    ])
    res = build_index(goal, ps, animals, mode=IndexMode.ECONOMIC_WEIGHT)
    codes = [i.code for i in res.validation.issues]
    assert "breed_restricted_trait" not in codes


def test_index_with_pap_solves_in_both_modes():
    """An index that includes PAP and latent PAP solves cleanly and
    produces finite, sensible index values in both modes."""
    ps = consensus_parameter_set()
    goal = BreedingGoal(
        name="PAP index", basis=EconomicBasis.PER_COW_EXPOSED,
        components=[
            GoalComponent("WW", 0.85), GoalComponent("PAP", -8.9),
            GoalComponent("PAP_L", -100.0),
        ],
    )
    animals = AnimalSet([
        _mk("A1", "Angus",
            {"WW": 30, "PAP": -3.0, "PAP_L": -0.4}),
        _mk("A2", "Angus",
            {"WW": 10, "PAP": 4.0, "PAP_L": 0.5}),
    ])
    for mode in (IndexMode.ECONOMIC_WEIGHT, IndexMode.BLUP_INDEX):
        res = build_index(goal, ps, animals, mode=mode)
        assert res.validation.ok
        for s in res.scores:
            assert np.isfinite(s.index_value)
            # Sane magnitude - not the 1e7 blow-up of an ill-conditioned
            # solve.
            assert abs(s.index_value) < 1e5
        # The lower-PAP animal (A1) should rank above the higher-PAP one.
        ranked = {s.animal_id: s.index_value for s in res.scores}
        assert ranked["A1"] > ranked["A2"]
