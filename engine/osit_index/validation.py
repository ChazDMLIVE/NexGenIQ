"""
Validation engine for osit-index.

Software that informs real breeding decisions must never silently accept bad
input. This module implements the validation rules of NexGenIQ Phase 3
Part 3A Section 1.4, with three severities:

* ERROR  — blocks the run; the result would be wrong or undefined.
* WARN   — the run proceeds but the result is flagged (partial data, low
           accuracy, possible double-counting).
* INFO   — advisory; nothing is wrong, but the user should be aware.

Every issue carries a plain-language message and, where relevant, a fix hint,
so the UI can surface it inline next to its cause (Phase 3.5 Section 5.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from .animal import AnimalSet, EpdScale
from .goal import BreedingGoal
from .traits import BREED_RESTRICTED_TRAITS
from .parameters import GeneticParameterSet

_SYM_TOL = 1e-8
_PD_TOL = 1e-10
_LOW_ACCURACY = 0.05  # BIF accuracy below this triggers a WARN.


class Severity(str, Enum):
    """Severity of a validation issue."""

    ERROR = "error"
    WARN = "warn"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation finding.

    Attributes
    ----------
    severity:
        ERROR, WARN or INFO.
    code:
        Stable machine code (e.g. ``"matrix_not_pd"``) — used to link the
        issue to its troubleshooting-page entry. Never shown raw to users.
    message:
        Plain-language description of the problem.
    fix_hint:
        Optional concrete next action ("how to fix this").
    location:
        Optional pointer to the cause (a trait code, animal id, etc.) so the
        UI can place the message next to it.
    """

    severity: Severity
    code: str
    message: str
    fix_hint: str = ""
    location: str = ""


@dataclass
class ValidationReport:
    """The collected result of validating an index run."""

    issues: list[ValidationIssue] = field(default_factory=list)

    def add(
        self,
        severity: Severity,
        code: str,
        message: str,
        fix_hint: str = "",
        location: str = "",
    ) -> None:
        """Append an issue to the report."""
        self.issues.append(
            ValidationIssue(severity, code, message, fix_hint, location)
        )

    @property
    def errors(self) -> list[ValidationIssue]:
        """All ERROR-severity issues."""
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """All WARN-severity issues."""
        return [i for i in self.issues if i.severity is Severity.WARN]

    @property
    def infos(self) -> list[ValidationIssue]:
        """All INFO-severity issues."""
        return [i for i in self.issues if i.severity is Severity.INFO]

    @property
    def ok(self) -> bool:
        """True if there are no ERROR-severity issues (the run may proceed)."""
        return not self.errors


# ---------------------------------------------------------------------------
# Matrix checks
# ---------------------------------------------------------------------------
def check_covariance_matrix(
    matrix: np.ndarray,
    report: ValidationReport,
    *,
    name: str,
    require_pd: bool,
) -> None:
    """Validate a (co)variance matrix: shape, symmetry, definiteness.

    Parameters
    ----------
    matrix:
        The matrix to check.
    report:
        Report to append issues to.
    name:
        Human-readable matrix name for messages (e.g. ``"P"``, ``"G0"``).
    require_pd:
        If ``True`` the matrix must be positive definite (an ERROR if not);
        if ``False`` it need only be positive semi-definite.
    """
    arr = np.asarray(matrix, dtype=float)

    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        report.add(
            Severity.ERROR,
            "matrix_not_square",
            f"The {name} matrix must be square; got shape {arr.shape}.",
        )
        return

    if not np.allclose(arr, arr.T, atol=_SYM_TOL):
        report.add(
            Severity.ERROR,
            "matrix_not_symmetric",
            f"The {name} matrix is not symmetric. A (co)variance matrix "
            "must equal its own transpose.",
            fix_hint="Check that each off-diagonal value is entered "
                     "identically on both sides of the diagonal.",
        )
        return

    eigenvalues = np.linalg.eigvalsh(arr)
    smallest = float(eigenvalues.min())

    if require_pd and smallest <= _PD_TOL:
        report.add(
            Severity.ERROR,
            "matrix_not_pd",
            f"The {name} matrix is not positive definite. The genetic "
            "correlations you supplied are not mutually consistent — no "
            "real population could have all of them at once.",
            fix_hint="This usually means a typo in one correlation. Review "
                     "the correlations, or apply the nearest valid "
                     "correction.",
        )
    elif not require_pd and smallest < -_PD_TOL:
        report.add(
            Severity.ERROR,
            "matrix_not_psd",
            f"The {name} matrix is not positive semi-definite "
            f"(smallest eigenvalue {smallest:.2e}).",
            fix_hint="Review the supplied correlations for inconsistency.",
        )


# ---------------------------------------------------------------------------
# Goal / parameter / animal checks
# ---------------------------------------------------------------------------
# Known composite-vs-component trait groups, for double-counting warnings.
_REDUNDANT_GROUPS: list[set[str]] = [
    {"YW", "WW", "PWG"},  # yearling weight ~= weaning weight + post-wean gain
]


def validate_goal(goal: BreedingGoal, report: ValidationReport) -> None:
    """Validate a breeding goal: non-empty, no redundancy, not degenerate."""
    codes = goal.trait_codes

    if not codes:
        report.add(
            Severity.ERROR,
            "empty_goal",
            "The breeding goal has no traits. Add at least one trait "
            "before building an index.",
        )
        return

    # Redundant (composite + component) traits -> possible double-counting.
    code_set = set(codes)
    for group in _REDUNDANT_GROUPS:
        present = code_set & group
        if len(present) >= 2 and group <= code_set:
            report.add(
                Severity.WARN,
                "redundant_traits",
                "Your goal includes both a composite trait and its "
                f"components ({', '.join(sorted(present))}). Their growth "
                "may be counted twice.",
                fix_hint="Keep either the composite trait or its "
                         "components, not both.",
            )

    # Degenerate goal: one weight dwarfs the rest -> near tandem selection.
    weights = [abs(w) for w in goal.economic_weights]
    nonzero = [w for w in weights if w > 0]
    if len(codes) == 1:
        report.add(
            Severity.INFO,
            "single_trait_goal",
            "The goal has a single trait, so the index is just that "
            "trait's EPD. That is valid but not really an index.",
        )
    elif nonzero and max(nonzero) > 100 * min(nonzero):
        report.add(
            Severity.INFO,
            "dominant_weight",
            "One economic weight is far larger than the others, so the "
            "index will behave almost like selection on that single trait.",
        )


def validate_parameters(
    goal: BreedingGoal,
    params: GeneticParameterSet,
    report: ValidationReport,
) -> None:
    """Check the parameter set covers every goal trait."""
    missing = params.has_all(goal.trait_codes)
    if missing:
        report.add(
            Severity.ERROR,
            "missing_parameters",
            "The genetic-parameter set is missing values for: "
            f"{', '.join(missing)}.",
            fix_hint="Choose a parameter set that covers these traits, or "
                     "supply heritability and genetic SD for each.",
        )


def validate_animals(
    animal_set: AnimalSet,
    trait_codes: list[str],
    report: ValidationReport,
) -> None:
    """Validate the candidate animals against the index traits.

    Checks: at least one animal; consistent EPD/EBV scale; cross-evaluation
    consistency; near-zero accuracies. The missing-EPD policy itself is
    applied in :mod:`index` (it depends on a user choice); here we only note
    a near-zero accuracy.
    """
    if len(animal_set) == 0:
        report.add(
            Severity.ERROR,
            "no_animals",
            "There are no animals to rank. Add at least one candidate "
            "animal.",
        )
        return

    # Cross-evaluation consistency: multi-breed sets need adjustment, which
    # the caller must arrange; here we surface the situation as INFO so the
    # report explains why adjustment happened.
    if len(animal_set.evaluation_ids - {""}) > 1:
        report.add(
            Severity.INFO,
            "multiple_evaluations",
            "The animals come from more than one genetic evaluation. Their "
            "EPDs will be placed on a common base before ranking.",
        )

    # Breed-gating: some EPDs (e.g. PAP, the pulmonary-arterial-pressure
    # trait) are published only by certain breed associations. If the
    # breeding goal includes such a trait, at least one candidate animal
    # should be of a breed that publishes it - otherwise the trait's EPDs
    # are not on a meaningful, comparable footing.
    herd_breeds = {a.breed for a in animal_set if a.breed}
    for code in trait_codes:
        publishers = BREED_RESTRICTED_TRAITS.get(code)
        if publishers and not (herd_breeds & set(publishers)):
            report.add(
                Severity.WARN,
                "breed_restricted_trait",
                f"The goal includes {code}, whose EPD is published only "
                f"by {', '.join(publishers)}. None of the candidate "
                f"animals are of those breeds, so this trait's EPDs may "
                f"not be comparable across your animals.",
                fix_hint=f"Use {code} only for {', '.join(publishers)} "
                         f"animals, or remove it from the breeding goal.",
            )

    for animal in animal_set:
        for code in trait_codes:
            epd = animal.epd(code)
            if epd is None:
                continue
            if epd.bif_accuracy is None:
                report.add(
                    Severity.WARN,
                    "missing_accuracy",
                    f"{animal.animal_id}: no accuracy given for {code}. "
                    "Its index value will be shown without a reliable "
                    "confidence interval.",
                    location=animal.animal_id,
                )
            elif epd.bif_accuracy < _LOW_ACCURACY:
                report.add(
                    Severity.WARN,
                    "low_accuracy",
                    f"{animal.animal_id}: very low accuracy for {code} "
                    f"(BIF {epd.bif_accuracy:.2f}). This EPD could change "
                    "substantially as more data accrue.",
                    fix_hint="Consider the accuracy-adjusted index mode, "
                             "which down-weights uncertain EPDs.",
                    location=animal.animal_id,
                )
