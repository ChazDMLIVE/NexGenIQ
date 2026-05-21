"""
Genetic parameters for osit-index.

This module holds the population-level genetic parameters the index engine
needs — heritabilities, genetic standard deviations, and the genetic /
phenotypic correlation structure — and the accuracy-scale conversions defined
by the Beef Improvement Federation.

Reference: NexGenIQ Phase 1 Sections 1.4 and 2.4; Phase 3 Part 3B Section 2.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Numerical tolerance used for symmetry / positive-definiteness checks.
_TOL = 1e-8


def nearest_pd_correlation(corr: np.ndarray, eps: float = 0.01) -> np.ndarray:
    """Return the nearest valid correlation matrix to ``corr``.

    Genetic correlations elicited from the literature are assembled
    pairwise and need not form a jointly consistent (positive-definite)
    matrix - one trait can be reported as strongly correlated with several
    others in ways that cannot all hold at once. A selection index built
    on such a set would have a singular or indefinite covariance matrix
    and could not be solved.

    This function projects the supplied symmetric matrix onto the nearest
    positive-definite correlation matrix: it clips the eigenvalues to a
    small positive floor, reconstitutes the matrix, and rescales the
    diagonal back to one. It is a standard, well-documented repair for
    elicited correlation matrices (Higham, 2002). The repair is small
    when the input is already close to valid, and the engine records that
    a repair was applied so the result is never silently changed.

    Parameters
    ----------
    corr:
        A symmetric matrix with a unit diagonal.
    eps:
        The positive floor applied to the eigenvalues. The default of
        0.01 does more than make the matrix barely positive-definite: it
        keeps it *well-conditioned*. A floor at machine epsilon would
        leave a near-singular matrix whose inverse (needed for the
        BLUP-index solve b = P^-1 G a) is numerically unstable and
        produces meaningless index values. A 0.01 floor caps the
        condition number in the low hundreds while moving the elicited
        correlations only marginally more than a machine-epsilon floor
        would.

    Returns
    -------
    numpy.ndarray
        The nearest well-conditioned positive-definite correlation
        matrix.
    """
    arr = np.asarray(corr, dtype=float)
    # Symmetrise defensively, then eigen-decompose.
    sym = 0.5 * (arr + arr.T)
    eigvals, eigvecs = np.linalg.eigh(sym)
    if eigvals.min() > eps:
        return sym  # already positive-definite - nothing to repair
    # Clip eigenvalues to a positive floor and rebuild.
    clipped = np.clip(eigvals, eps, None)
    rebuilt = (eigvecs * clipped) @ eigvecs.T
    # Rescale so the diagonal is exactly one again (a true correlation
    # matrix). d^-1/2 R d^-1/2.
    d = np.sqrt(np.diag(rebuilt))
    scaled = rebuilt / np.outer(d, d)
    # Symmetrise once more to remove tiny floating-point asymmetry.
    return 0.5 * (scaled + scaled.T)


def is_positive_definite(matrix: np.ndarray, tol: float = _TOL) -> bool:
    """Return True if ``matrix`` is symmetric positive-definite."""
    arr = np.asarray(matrix, dtype=float)
    if not np.allclose(arr, arr.T, atol=tol):
        return False
    return bool(np.linalg.eigvalsh(arr).min() > tol)


# ---------------------------------------------------------------------------
# BIF accuracy scale conversions (Phase 1 Section 1.4)
# ---------------------------------------------------------------------------
def bif_accuracy_to_reliability(bif_acc: float) -> float:
    """Convert a BIF accuracy to a reliability (r-squared).

    The Beef Improvement Federation defines accuracy as
    ``BIF_acc = 1 - sqrt(1 - reliability)``. Inverting,

        reliability = 1 - (1 - BIF_acc)**2

    Parameters
    ----------
    bif_acc:
        BIF accuracy in [0, 1].

    Returns
    -------
    float
        Reliability (squared theoretical accuracy) in [0, 1].

    Examples
    --------
    A BIF accuracy of 0.50 corresponds to a reliability of 0.75 — the
    conversion table in Phase 1 Section 1.4.1.

    >>> round(bif_accuracy_to_reliability(0.50), 4)
    0.75
    """
    if not 0.0 <= bif_acc <= 1.0:
        raise ValueError(f"BIF accuracy must be in [0, 1], got {bif_acc}.")
    return 1.0 - (1.0 - bif_acc) ** 2


def bif_accuracy_to_theoretical(bif_acc: float) -> float:
    """Convert a BIF accuracy to a theoretical accuracy (correlation r).

    ``r = sqrt(reliability) = sqrt(1 - (1 - BIF_acc)**2)``.
    """
    return float(np.sqrt(bif_accuracy_to_reliability(bif_acc)))


def reliability_to_bif_accuracy(reliability: float) -> float:
    """Convert a reliability (r-squared) back to a BIF accuracy.

    Inverse of :func:`bif_accuracy_to_reliability`:
    ``BIF_acc = 1 - sqrt(1 - reliability)``.
    """
    if not 0.0 <= reliability <= 1.0:
        raise ValueError(
            f"Reliability must be in [0, 1], got {reliability}."
        )
    return 1.0 - float(np.sqrt(1.0 - reliability))


# ---------------------------------------------------------------------------
# Per-trait parameters
# ---------------------------------------------------------------------------
@dataclass
class TraitParameters:
    """Genetic parameters for one trait.

    Attributes
    ----------
    trait_code:
        The trait this row describes (matches :data:`traits.TRAIT_REGISTRY`).
    heritability:
        Narrow-sense heritability h^2, in (0, 1]. The additive proportion of
        phenotypic variance (Phase 1 Section 3.1).
    genetic_sd:
        Additive genetic standard deviation sigma_u, in the trait's units.
        Needed to turn correlations into covariances and to scale possible
        change.
    citation:
        Literature source for these values, surfaced in the help system so
        every default is traceable.
    """

    trait_code: str
    heritability: float
    genetic_sd: float
    citation: str = ""

    def __post_init__(self) -> None:
        if not 0.0 < self.heritability <= 1.0:
            raise ValueError(
                f"Heritability for {self.trait_code} must be in (0, 1], "
                f"got {self.heritability}."
            )
        if self.genetic_sd <= 0.0:
            raise ValueError(
                f"Genetic SD for {self.trait_code} must be positive, "
                f"got {self.genetic_sd}."
            )


# ---------------------------------------------------------------------------
# Full parameter set
# ---------------------------------------------------------------------------
@dataclass
class GeneticParameterSet:
    """A complete genetic-parameter set: per-trait parameters plus the
    genetic correlation structure among traits.

    The engine stores correlations (dimensionless, easy to validate and to
    source from literature) and derives covariance matrices on demand. The
    phenotypic correlation matrix is optional; when omitted it is only needed
    for raw-phenotype information sources, which the MVP does not use.

    Attributes
    ----------
    name:
        Human-readable identifier (e.g. ``"Beef-cattle consensus set"``).
    version:
        Version string recorded in the reproducibility ledger.
    trait_params:
        Mapping of trait code -> :class:`TraitParameters`.
    genetic_correlations:
        Mapping of frozenset({code_a, code_b}) -> genetic correlation r_g.
        A pair absent from the mapping is treated as r_g = 0. The diagonal
        (a trait with itself) is always 1 and need not be supplied.
    """

    name: str
    version: str
    trait_params: dict[str, TraitParameters] = field(default_factory=dict)
    genetic_correlations: dict[frozenset[str], float] = field(
        default_factory=dict
    )

    # -- lookups ------------------------------------------------------------
    def heritability(self, code: str) -> float:
        """Return the heritability for trait ``code``."""
        return self.trait_params[code].heritability

    def genetic_sd(self, code: str) -> float:
        """Return the additive genetic SD for trait ``code``."""
        return self.trait_params[code].genetic_sd

    def genetic_correlation(self, code_a: str, code_b: str) -> float:
        """Return the genetic correlation between two traits.

        Returns 1.0 for a trait with itself, and 0.0 for any pair not
        explicitly supplied.
        """
        if code_a == code_b:
            return 1.0
        return self.genetic_correlations.get(
            frozenset({code_a, code_b}), 0.0
        )

    # -- derived matrices ---------------------------------------------------
    def _raw_correlation_matrix(self, codes: list[str]) -> np.ndarray:
        """Build the genetic correlation matrix exactly as elicited."""
        n = len(codes)
        corr = np.eye(n)
        for j in range(n):
            for k in range(j + 1, n):
                r = self.genetic_correlation(codes[j], codes[k])
                corr[j, k] = corr[k, j] = r
        return corr

    def correlation_was_repaired(self, codes: list[str]) -> bool:
        """Return True if the elicited correlation matrix for ``codes`` is
        not positive-definite and would therefore be repaired before use.

        The validation layer surfaces this to the user as an information
        note so a repaired matrix is never used silently.
        """
        return not is_positive_definite(self._raw_correlation_matrix(codes))

    def genetic_correlation_matrix(
        self, codes: list[str], repair: bool = True
    ) -> np.ndarray:
        """Build the genetic correlation matrix for ``codes`` (diagonal 1).

        Parameters
        ----------
        codes:
            Ordered list of trait codes.
        repair:
            If ``True`` (the default) and the elicited matrix is not
            positive-definite, return the nearest valid correlation
            matrix (see :func:`nearest_pd_correlation`). Pairwise-elicited
            literature correlations need not be jointly consistent; the
            repair guarantees a solvable selection index. Pass ``False``
            to obtain the unrepaired elicited matrix (e.g. for the
            validation layer to detect that a repair is needed).
        """
        corr = self._raw_correlation_matrix(codes)
        if repair and not is_positive_definite(corr):
            return nearest_pd_correlation(corr)
        return corr

    def genetic_covariance_matrix(
        self, codes: list[str], repair: bool = True
    ) -> np.ndarray:
        """Build the additive genetic (co)variance matrix G0 for ``codes``.

        Element (j, k) is ``r_g(j,k) * sigma_u,j * sigma_u,k``. The result
        is symmetric by construction.

        Parameters
        ----------
        codes:
            Ordered list of trait codes. The returned matrix follows this
            order on both axes.
        repair:
            If ``True`` (the default), the genetic correlation matrix is
            repaired to the nearest positive-definite matrix when the
            elicited values are not jointly consistent, so the resulting
            G0 is always a valid covariance matrix and the index is
            always solvable.
        """
        sd = np.array([self.genetic_sd(c) for c in codes])
        corr = self.genetic_correlation_matrix(codes, repair=repair)
        # G0 = D corr D, with D = diag(sigma_u).
        return np.outer(sd, sd) * corr

    def has_all(self, codes: list[str]) -> list[str]:
        """Return the subset of ``codes`` missing per-trait parameters.

        An empty list means every requested trait is covered.
        """
        return [c for c in codes if c not in self.trait_params]
