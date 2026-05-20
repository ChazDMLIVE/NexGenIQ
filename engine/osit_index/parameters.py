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
    def genetic_covariance_matrix(self, codes: list[str]) -> np.ndarray:
        """Build the additive genetic (co)variance matrix G0 for ``codes``.

        Element (j, k) is ``r_g(j,k) * sigma_u,j * sigma_u,k``. The result is
        symmetric by construction; positive-definiteness is the caller's
        concern (it is validated in :mod:`validation`).

        Parameters
        ----------
        codes:
            Ordered list of trait codes. The returned matrix follows this
            order on both axes.
        """
        n = len(codes)
        sd = np.array([self.genetic_sd(c) for c in codes])
        corr = np.eye(n)
        for j in range(n):
            for k in range(j + 1, n):
                r = self.genetic_correlation(codes[j], codes[k])
                corr[j, k] = corr[k, j] = r
        # G0 = D corr D, with D = diag(sigma_u).
        return np.outer(sd, sd) * corr

    def genetic_correlation_matrix(self, codes: list[str]) -> np.ndarray:
        """Build the genetic correlation matrix for ``codes`` (diagonal 1)."""
        n = len(codes)
        corr = np.eye(n)
        for j in range(n):
            for k in range(j + 1, n):
                r = self.genetic_correlation(codes[j], codes[k])
                corr[j, k] = corr[k, j] = r
        return corr

    def has_all(self, codes: list[str]) -> list[str]:
        """Return the subset of ``codes`` missing per-trait parameters.

        An empty list means every requested trait is covered.
        """
        return [c for c in codes if c not in self.trait_params]
