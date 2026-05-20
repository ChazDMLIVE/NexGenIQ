"""
The selection-index core of osit-index.

This module constructs an economic selection index and ranks candidate
animals. It is the mathematical heart of NexGenIQ: everything else in the
package either prepares this module's inputs or consumes its output.

The index is the predictor I = b'x of the breeding goal H = a'g. The index
weights solve the Smith (1936) / Hazel (1943) selection-index equations:

    P b = G a        =>        b = P^-1 G a

* ECONOMIC_WEIGHT mode sets b = a directly — the transparent form breed
  associations publish, correct when EPD accuracies are similar. Default.
* BLUP_INDEX mode solves the full system, down-weighting low-accuracy and
  correlated information sources.

Reference: NexGenIQ Phase 1 Section 2.2; Phase 3 Part 3B Section 2.2.
All matrix construction follows Phase 3 Part 3B Section 2.2.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from .adjustment import (
    AdjustmentFactorTable,
    AdjustmentRecord,
    apply_across_breed_adjustment,
)
from .animal import AnimalSet
from .goal import BreedingGoal
from .parameters import GeneticParameterSet, bif_accuracy_to_reliability
from .validation import (
    Severity,
    ValidationReport,
    check_covariance_matrix,
    validate_animals,
    validate_goal,
    validate_parameters,
)


class IndexMode(str, Enum):
    """How the index combines economic weights and EPDs.

    ECONOMIC_WEIGHT
        b = a. The index is the economically weighted sum of EPDs. The
        transparent default (Phase 3 Appendix A.1).
    BLUP_INDEX
        b = P^-1 G a. The full selection-index solution, which additionally
        accounts for the accuracy and correlation structure of the EPDs.
    """

    ECONOMIC_WEIGHT = "economic_weight"
    BLUP_INDEX = "blup_index"


class MissingEpdPolicy(str, Enum):
    """What to do when an animal lacks an EPD for an index trait."""

    EXCLUDE = "exclude"     # drop the animal, with a warning (default)
    IMPUTE_MEAN = "impute"  # substitute 0 (the breed-base mean), flag partial


# ---------------------------------------------------------------------------
# Matrix construction (Phase 3 Part 3B Section 2.2.1)
# ---------------------------------------------------------------------------
def _reliabilities(
    animal_set: AnimalSet, codes: list[str]
) -> dict[str, float]:
    """Mean reliability per trait across the animal set.

    The matrices P and G describe the (co)variance structure of the EPDs
    used as information sources. Accuracy varies per animal, but the index
    weights b are computed once for the whole set, so P and G use the mean
    reliability per trait. Per-animal accuracies are still used for the
    per-animal uncertainty in :func:`_score_animals`.

    A missing accuracy contributes a reliability of 0.
    """
    rels: dict[str, float] = {}
    for code in codes:
        vals = []
        for animal in animal_set:
            epd = animal.epd(code)
            if epd is None:
                continue
            if epd.bif_accuracy is None:
                vals.append(0.0)
            else:
                vals.append(bif_accuracy_to_reliability(epd.bif_accuracy))
        rels[code] = float(np.mean(vals)) if vals else 0.0
    return rels


def build_P_matrix(
    codes: list[str],
    params: GeneticParameterSet,
    reliabilities: dict[str, float],
) -> np.ndarray:
    """Build the (co)variance matrix P among the EPD information sources.

    For EPD k of additive genetic SD ``sigma_u,k`` and reliability
    ``rel_k`` (Phase 3 Part 3B Section 2.2.1):

        Var(EPD_k)        = (1/4) * rel_k * sigma_u,k^2
        Cov(EPD_j, EPD_k) = (1/4) * sqrt(rel_j rel_k) * r_g(j,k)
                              * sigma_u,j * sigma_u,k

    The 1/4 places EPDs on the progeny-difference scale (EPD = EBV / 2, so
    Var(EPD) = Var(EBV) / 4).

    Returns
    -------
    numpy.ndarray
        The symmetric ``n x n`` matrix P, ``n = len(codes)``.
    """
    n = len(codes)
    sd = np.array([params.genetic_sd(c) for c in codes])
    rel = np.array([reliabilities[c] for c in codes])
    corr = params.genetic_correlation_matrix(codes)

    # sqrt(rel_j * rel_k) for every pair, as an outer product.
    rel_root = np.sqrt(np.outer(rel, rel))
    sd_outer = np.outer(sd, sd)
    P = 0.25 * rel_root * corr * sd_outer
    # Force exact symmetry against floating-point drift.
    return 0.5 * (P + P.T)


def build_G_matrix(
    info_codes: list[str],
    goal_codes: list[str],
    params: GeneticParameterSet,
    reliabilities: dict[str, float],
) -> np.ndarray:
    """Build the covariance matrix G between EPDs and goal-trait breeding
    values.

    Element (j, k) is the covariance between information source EPD j and
    goal trait k's breeding value (Phase 3 Part 3B Section 2.2.1):

        G(j, k) = (1/2) * sqrt(rel_j) * r_g(j,k) * sigma_u,j * sigma_u,k

    The 1/2 converts the EPD scale to the breeding-value scale.

    Returns
    -------
    numpy.ndarray
        The ``n x m`` matrix G (``n`` information sources, ``m`` goal traits).
    """
    n, m = len(info_codes), len(goal_codes)
    G = np.zeros((n, m))
    for j, jc in enumerate(info_codes):
        rel_j = reliabilities[jc]
        sd_j = params.genetic_sd(jc)
        for k, kc in enumerate(goal_codes):
            sd_k = params.genetic_sd(kc)
            r_g = params.genetic_correlation(jc, kc)
            G[j, k] = 0.5 * np.sqrt(rel_j) * r_g * sd_j * sd_k
    return G


def solve_index_weights(
    P: np.ndarray,
    G: np.ndarray,
    a: np.ndarray,
) -> np.ndarray:
    """Solve the selection-index equations ``P b = G a`` for ``b``.

    The solution ``b = P^-1 G a`` is computed via Cholesky factorisation of
    P followed by triangular solves — P is never explicitly inverted, which
    is both more numerically stable and faster (Phase 3 Part 3B Section
    2.2.2).

    Parameters
    ----------
    P:
        The ``n x n`` symmetric positive-definite information-source
        (co)variance matrix.
    G:
        The ``n x m`` information-source / goal-trait covariance matrix.
    a:
        The ``m``-vector of economic weights.

    Returns
    -------
    numpy.ndarray
        The ``n``-vector of index weights ``b``.

    Raises
    ------
    numpy.linalg.LinAlgError
        If P is not positive definite (Cholesky factorisation fails). The
        caller should have screened this with the validation layer first.
    """
    P = np.asarray(P, dtype=float)
    G = np.asarray(G, dtype=float)
    a = np.asarray(a, dtype=float)

    w = G @ a                       # right-hand side, an n-vector
    cho = cho_factor(P, lower=True, check_finite=True)
    b = cho_solve(cho, w, check_finite=True)
    return b


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
@dataclass
class AnimalScore:
    """The index result for one animal.

    Attributes
    ----------
    animal_id:
        The animal's identifier.
    breed:
        The animal's breed.
    index_value:
        The index value I = b'x.
    std_error:
        Standard error of the index value, from propagating EPD accuracies
        (Phase 3 Part 3B Section 2.2.4). ``None`` if accuracies were absent.
    ci_low, ci_high:
        Bounds of the 95% confidence interval, or ``None``.
    contributions:
        Mapping of trait code -> that trait's contribution ``b_k * x_k`` to
        the index value. Lets the UI explain *why* an animal ranks where it
        does.
    rank:
        1-based rank within the scored set (1 = best). Filled after sorting.
    is_partial:
        ``True`` if any index trait's EPD was imputed rather than supplied.
    """

    animal_id: str
    breed: str
    index_value: float
    std_error: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    contributions: dict[str, float] = field(default_factory=dict)
    rank: int = 0
    is_partial: bool = False


@dataclass
class IndexResult:
    """The full output of :func:`build_index`.

    Attributes
    ----------
    weights:
        Mapping of trait code -> index weight ``b_k``.
    scores:
        Candidate animals, ranked best-first.
    validation:
        The :class:`ValidationReport` for the run.
    mode:
        The :class:`IndexMode` used.
    excluded:
        Ids of animals dropped under the EXCLUDE missing-EPD policy.
    adjustment_records:
        Across-breed adjustments applied (empty if none).
    adjustment_table_version:
        Version of the adjustment-factor table used (``""`` if none).
    info_codes:
        Ordered information-source trait codes (the index's traits).
    """

    weights: dict[str, float] = field(default_factory=dict)
    scores: list[AnimalScore] = field(default_factory=list)
    validation: ValidationReport = field(default_factory=ValidationReport)
    mode: IndexMode = IndexMode.ECONOMIC_WEIGHT
    excluded: list[str] = field(default_factory=list)
    adjustment_records: list[AdjustmentRecord] = field(default_factory=list)
    adjustment_table_version: str = ""
    info_codes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def _score_animals(
    animal_set: AnimalSet,
    info_codes: list[str],
    b: np.ndarray,
    params: GeneticParameterSet,
    missing_policy: MissingEpdPolicy,
    report: ValidationReport,
) -> tuple[list[AnimalScore], list[str]]:
    """Score every animal: index value, per-trait contribution, uncertainty.

    Returns the list of :class:`AnimalScore` (unranked) and the list of
    excluded animal ids.
    """
    b_map = dict(zip(info_codes, b))
    corr = params.genetic_correlation_matrix(info_codes)
    sd = np.array([params.genetic_sd(c) for c in info_codes])

    scores: list[AnimalScore] = []
    excluded: list[str] = []

    for animal in animal_set:
        missing = animal.has_traits(info_codes)
        if missing and missing_policy is MissingEpdPolicy.EXCLUDE:
            excluded.append(animal.animal_id)
            report.add(
                Severity.WARN,
                "animal_excluded",
                f"{animal.animal_id} was excluded — it has no EPD for: "
                f"{', '.join(missing)}.",
                location=animal.animal_id,
            )
            continue

        # Build the animal's EPD vector x (on the EPD scale) and its
        # per-trait reliabilities for the uncertainty calculation.
        x = np.zeros(len(info_codes))
        rels = np.zeros(len(info_codes))
        for i, code in enumerate(info_codes):
            epd = animal.epd(code)
            if epd is None:  # IMPUTE_MEAN policy: 0 == breed-base mean
                x[i] = 0.0
                rels[i] = 0.0
            else:
                x[i] = epd.value_as_epd()
                rels[i] = (
                    bif_accuracy_to_reliability(epd.bif_accuracy)
                    if epd.bif_accuracy is not None
                    else 0.0
                )

        index_value = float(b @ x)
        contributions = {
            code: float(b_map[code] * x[i])
            for i, code in enumerate(info_codes)
        }

        # Uncertainty: Var(I) = b' S b, with S the animal's own EPD
        # (co)variance matrix (Phase 3 Part 3B Section 2.2.4). S is built
        # exactly like P but using this animal's accuracies.
        std_error: float | None = None
        ci_low: float | None = None
        ci_high: float | None = None
        if np.any(rels > 0):
            rel_root = np.sqrt(np.outer(rels, rels))
            S = 0.25 * rel_root * corr * np.outer(sd, sd)
            var_I = float(b @ S @ b)
            std_error = float(np.sqrt(max(var_I, 0.0)))
            ci_low = index_value - 1.96 * std_error
            ci_high = index_value + 1.96 * std_error

        scores.append(
            AnimalScore(
                animal_id=animal.animal_id,
                breed=animal.breed,
                index_value=index_value,
                std_error=std_error,
                ci_low=ci_low,
                ci_high=ci_high,
                contributions=contributions,
                is_partial=bool(missing),
            )
        )
        if missing and missing_policy is MissingEpdPolicy.IMPUTE_MEAN:
            report.add(
                Severity.WARN,
                "animal_partial",
                f"{animal.animal_id}: missing EPD(s) for "
                f"{', '.join(missing)} were treated as breed average. Its "
                "index value is approximate.",
                location=animal.animal_id,
            )

    return scores, excluded


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------
def build_index(
    goal: BreedingGoal,
    params: GeneticParameterSet,
    animal_set: AnimalSet,
    *,
    mode: IndexMode = IndexMode.ECONOMIC_WEIGHT,
    missing_policy: MissingEpdPolicy = MissingEpdPolicy.EXCLUDE,
    adjustment_table: AdjustmentFactorTable | None = None,
    native_multi_breed: bool = False,
    user_factors: dict[tuple[str, str], float] | None = None,
) -> IndexResult:
    """Construct an economic selection index and rank candidate animals.

    This is the top-level entry point of osit-index. It runs the full
    pipeline of Phase 3 Part 3B Section 2.2.5: validate, across-breed
    adjust, build P and G, solve for the index weights, score and rank.

    Parameters
    ----------
    goal:
        The breeding goal (goal traits + economic weights).
    params:
        The genetic-parameter set.
    animal_set:
        The candidate animals to rank.
    mode:
        ECONOMIC_WEIGHT (default) or BLUP_INDEX.
    missing_policy:
        How to handle animals missing an index trait's EPD.
    adjustment_table:
        Across-breed adjustment factors. Required for a multi-breed set
        unless ``native_multi_breed`` is set.
    native_multi_breed:
        Set ``True`` if all EPDs come from one multi-breed evaluation.
    user_factors:
        Optional user-supplied across-breed factors for pairs the published
        table does not cover.

    Returns
    -------
    IndexResult
        Index weights, ranked animal scores, the validation report and run
        metadata. If validation produced an ERROR, the result carries the
        report and empty scores — the run does not proceed.
    """
    report = ValidationReport()

    # In the MVP the information sources are the goal traits themselves.
    info_codes = list(goal.trait_codes)

    # --- Step 1-3: validate goal, parameters, animals --------------------
    validate_goal(goal, report)
    validate_parameters(goal, params, report)
    validate_animals(animal_set, info_codes, report)
    if not report.ok:
        return IndexResult(validation=report, mode=mode, info_codes=info_codes)

    # --- Step 4: across-breed adjustment ---------------------------------
    try:
        adj = apply_across_breed_adjustment(
            animal_set,
            info_codes,
            adjustment_table,
            native_multi_breed=native_multi_breed,
            user_factors=user_factors,
        )
    except ValueError as exc:
        report.add(
            Severity.ERROR,
            "adjustment_unavailable",
            str(exc),
            fix_hint="Provide an adjustment factor for each listed "
                     "breed/trait pair, or drop the affected trait.",
        )
        return IndexResult(validation=report, mode=mode, info_codes=info_codes)
    working_set = adj.animal_set

    # --- Step 5: build P and G ------------------------------------------
    rels = _reliabilities(working_set, info_codes)
    P = build_P_matrix(info_codes, params, rels)
    G0 = params.genetic_covariance_matrix(info_codes)

    # G0 underpins both modes; verify it is a valid (co)variance matrix.
    check_covariance_matrix(G0, report, name="G0", require_pd=False)

    a = np.array(goal.economic_weights, dtype=float)

    # --- Step 6-7: solve for index weights -------------------------------
    if mode is IndexMode.ECONOMIC_WEIGHT:
        # Economic-weight index: b = a directly (Phase 1 Section 2.2.4).
        b = a.copy()
    else:
        # BLUP-index: solve b = P^-1 G a. Needs a positive-definite P.
        check_covariance_matrix(P, report, name="P", require_pd=True)
        if not report.ok:
            return IndexResult(
                validation=report, mode=mode, info_codes=info_codes
            )
        G = build_G_matrix(info_codes, info_codes, params, rels)
        b = solve_index_weights(P, G, a)

    # --- Step 8-10: score, rank ------------------------------------------
    scores, excluded = _score_animals(
        working_set, info_codes, b, params, missing_policy, report
    )
    scores.sort(key=lambda s: s.index_value, reverse=True)
    for i, score in enumerate(scores, start=1):
        score.rank = i

    return IndexResult(
        weights=dict(zip(info_codes, b)),
        scores=scores,
        validation=report,
        mode=mode,
        excluded=excluded,
        adjustment_records=adj.records,
        adjustment_table_version=adj.table_version,
        info_codes=info_codes,
    )
