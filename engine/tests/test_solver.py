"""
Tests for the selection-index solver: b = P^-1 G a.

These are the correctness-critical numerical tests. The solver is verified
against (a) an independent linear-algebra solve, (b) hand-worked closed-form
cases, and (c) the documented consistency property that the BLUP-index
collapses to the economic-weight index in the uniform-accuracy limit
(Phase 1 Section 2.2.4; Phase 3 Part 3D Section 4.3).
"""

import numpy as np
import pytest

from osit_index.index import (
    IndexMode,
    build_P_matrix,
    build_G_matrix,
    build_index,
    solve_index_weights,
)
from osit_index.parameters import GeneticParameterSet, TraitParameters


def test_solver_matches_numpy_solve():
    """b = P^-1 G a matches an independent numpy.linalg.solve on G a."""
    rng = np.random.default_rng(42)
    for n in (2, 3, 5, 8):
        # A random symmetric positive-definite P.
        A = rng.standard_normal((n, n))
        P = A @ A.T + n * np.eye(n)
        G = rng.standard_normal((n, n))
        a = rng.standard_normal(n)

        b = solve_index_weights(P, G, a)
        b_ref = np.linalg.solve(P, G @ a)
        np.testing.assert_allclose(b, b_ref, rtol=1e-10, atol=1e-12)


def test_solver_satisfies_the_equations():
    """The returned b actually satisfies P b = G a."""
    rng = np.random.default_rng(7)
    n = 4
    A = rng.standard_normal((n, n))
    P = A @ A.T + n * np.eye(n)
    G = rng.standard_normal((n, n))
    a = rng.standard_normal(n)

    b = solve_index_weights(P, G, a)
    np.testing.assert_allclose(P @ b, G @ a, rtol=1e-10, atol=1e-12)


def test_solver_handworked_two_trait():
    """A hand-worked 2x2 case solved on paper.

    P = [[2, 0], [0, 4]], G = identity, a = [3, 5].
    b = P^-1 a = [3/2, 5/4] = [1.5, 1.25].
    """
    P = np.array([[2.0, 0.0], [0.0, 4.0]])
    G = np.eye(2)
    a = np.array([3.0, 5.0])
    b = solve_index_weights(P, G, a)
    np.testing.assert_allclose(b, [1.5, 1.25], rtol=1e-12)


def test_solver_rejects_non_pd():
    """A non-positive-definite P makes the Cholesky-based solver raise."""
    P = np.array([[1.0, 2.0], [2.0, 1.0]])  # eigenvalues 3 and -1
    G = np.eye(2)
    a = np.array([1.0, 1.0])
    with pytest.raises(np.linalg.LinAlgError):
        solve_index_weights(P, G, a)


def _uniform_set(codes, h2=0.4, sd=20.0, corr=0.0):
    """A parameter set where all traits share h2, SD and pairwise corr."""
    tp = {c: TraitParameters(c, h2, sd) for c in codes}
    cors = {}
    for i, ci in enumerate(codes):
        for cj in codes[i + 1:]:
            cors[frozenset({ci, cj})] = corr
    return GeneticParameterSet("uniform", "test", tp, cors)


def test_blup_collapses_to_economic_weight_uniform_uncorrelated():
    """Key consistency property (Phase 1 Section 2.2.4).

    When all information sources have equal accuracy and zero genetic
    correlation, the BLUP-index weights b = P^-1 G a are proportional to
    the economic weights a — so the BLUP ranking equals the economic-weight
    ranking. We verify the proportionality of b to a directly.
    """
    codes = ["WW", "CED", "STAY"]
    params = _uniform_set(codes, h2=0.4, sd=20.0, corr=0.0)
    rels = {c: 0.5 for c in codes}  # equal reliability for every trait

    P = build_P_matrix(codes, params, rels)
    G = build_G_matrix(codes, codes, params, rels)
    a = np.array([3.0, 7.0, 2.0])

    b = solve_index_weights(P, G, a)
    # b should be a scalar multiple of a.
    ratios = b / a
    np.testing.assert_allclose(ratios, ratios[0], rtol=1e-9)


def test_blup_and_economic_weight_rank_identically_uniform(
    maternal_goal, params, angus_animals
):
    """End to end: with equal accuracies the two index modes rank the same.

    We give every EPD the same accuracy, then confirm that ECONOMIC_WEIGHT
    and BLUP_INDEX modes produce the same ordering of animals.
    """
    # Force uniform accuracy across every EPD.
    for animal in angus_animals:
        for epd in animal.epds.values():
            epd.bif_accuracy = 0.60

    econ = build_index(maternal_goal, params, angus_animals,
                       mode=IndexMode.ECONOMIC_WEIGHT)
    blup = build_index(maternal_goal, params, angus_animals,
                       mode=IndexMode.BLUP_INDEX)

    assert econ.validation.ok and blup.validation.ok
    econ_order = [s.animal_id for s in econ.scores]
    blup_order = [s.animal_id for s in blup.scores]
    assert econ_order == blup_order


def test_P_matrix_is_symmetric():
    """The constructed P matrix is exactly symmetric."""
    codes = ["WW", "CED", "STAY"]
    params = _uniform_set(codes, corr=0.3)
    rels = {"WW": 0.6, "CED": 0.4, "STAY": 0.2}
    P = build_P_matrix(codes, params, rels)
    np.testing.assert_allclose(P, P.T, atol=1e-14)


def test_P_matrix_variance_formula():
    """A diagonal element of P equals (1/4) * rel * sigma_u^2."""
    codes = ["WW"]
    params = _uniform_set(codes, h2=0.4, sd=22.0)
    rels = {"WW": 0.75}
    P = build_P_matrix(codes, params, rels)
    expected = 0.25 * 0.75 * 22.0 ** 2
    assert P[0, 0] == pytest.approx(expected)
