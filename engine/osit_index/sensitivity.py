"""
Sensitivity analysis for osit-index.

Economic weights are derived from uncertain prices and genetic parameters are
estimated with error, so an index is never exact. Sensitivity analysis tells
the user how robust their ranking is — a ranking stable across plausible
inputs can be trusted; one that reorders when a price moves a little is
fragile and the user should know (Phase 1 Section 2.9).

The MVP implements one-at-a-time ("tornado") sensitivity: vary one economic
weight at a time and observe how the ranking responds. Monte-Carlo joint
sensitivity is a v1.1 feature.

Reference: NexGenIQ Phase 3 Part 3A Section 1.1.1; Part 3B Section 2.9.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .animal import AnimalSet
from .goal import BreedingGoal
from .index import IndexMode, MissingEpdPolicy, build_index
from .parameters import GeneticParameterSet


def _rank_correlation(order_a: list[str], order_b: list[str]) -> float:
    """Spearman rank correlation between two orderings of the same ids.

    Returns 1.0 for identical orderings, down toward -1.0 for reversed.
    Used as a compact, plain-language-friendly stability summary.
    """
    common = [aid for aid in order_a if aid in order_b]
    n = len(common)
    if n < 2:
        return 1.0
    rank_a = {aid: i for i, aid in enumerate(order_a)}
    rank_b = {aid: i for i, aid in enumerate(order_b)}
    d2 = sum((rank_a[aid] - rank_b[aid]) ** 2 for aid in common)
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


@dataclass
class TornadoEntry:
    """The sensitivity of the ranking to one economic weight.

    Attributes
    ----------
    trait_code:
        The trait whose economic weight was varied.
    low_factor, high_factor:
        The multipliers applied to the baseline weight (e.g. 0.8 and 1.2).
    rank_corr_low, rank_corr_high:
        Rank correlation of the perturbed ranking against the baseline at
        the low and high ends. Near 1.0 means the ranking barely moved.
    top_changed_low, top_changed_high:
        Whether the top-ranked animal changed at each end.
    """

    trait_code: str
    low_factor: float
    high_factor: float
    rank_corr_low: float
    rank_corr_high: float
    top_changed_low: bool
    top_changed_high: bool

    @property
    def max_disruption(self) -> float:
        """How much this weight disrupts the ranking (0 = none, 2 = max).

        Used to order the tornado chart — most disruptive trait first.
        """
        return (1.0 - self.rank_corr_low) + (1.0 - self.rank_corr_high)


@dataclass
class SensitivityResult:
    """The result of a tornado sensitivity analysis.

    Attributes
    ----------
    entries:
        One :class:`TornadoEntry` per economic weight, ordered most- to
        least-disruptive.
    baseline_top:
        Animal id ranked first in the unperturbed index.
    summary:
        A one-sentence plain-language stability statement for the UI.
    """

    entries: list[TornadoEntry] = field(default_factory=list)
    baseline_top: str = ""
    summary: str = ""


def tornado_sensitivity(
    goal: BreedingGoal,
    params: GeneticParameterSet,
    animal_set: AnimalSet,
    *,
    variation: float = 0.20,
    mode: IndexMode = IndexMode.ECONOMIC_WEIGHT,
    missing_policy: MissingEpdPolicy = MissingEpdPolicy.EXCLUDE,
    **build_kwargs,
) -> SensitivityResult:
    """Run one-at-a-time sensitivity on the economic weights.

    For each goal trait the economic weight is multiplied by
    ``(1 - variation)`` and ``(1 + variation)`` in turn, the index is
    rebuilt, and the perturbed ranking is compared with the baseline.

    Parameters
    ----------
    goal, params, animal_set:
        The same inputs as :func:`index.build_index`.
    variation:
        Fractional perturbation applied to each economic weight (0.20 = +/-20%).
    mode, missing_policy, build_kwargs:
        Passed through to :func:`index.build_index` so the sensitivity run
        mirrors the baseline run exactly.

    Returns
    -------
    SensitivityResult
        Per-weight tornado entries plus a plain-language summary.
    """
    baseline = build_index(
        goal, params, animal_set,
        mode=mode, missing_policy=missing_policy, **build_kwargs,
    )
    if not baseline.validation.ok or not baseline.scores:
        return SensitivityResult(summary="Sensitivity could not be run "
                                         "because the baseline index did "
                                         "not build.")

    baseline_order = [s.animal_id for s in baseline.scores]
    baseline_top = baseline_order[0]

    entries: list[TornadoEntry] = []
    for comp in goal.components:
        def perturbed_order(factor: float) -> list[str]:
            g = copy.deepcopy(goal)
            for c in g.components:
                if c.trait_code == comp.trait_code:
                    c.economic_weight *= factor
            res = build_index(
                g, params, animal_set,
                mode=mode, missing_policy=missing_policy, **build_kwargs,
            )
            return [s.animal_id for s in res.scores]

        low_order = perturbed_order(1.0 - variation)
        high_order = perturbed_order(1.0 + variation)

        entries.append(
            TornadoEntry(
                trait_code=comp.trait_code,
                low_factor=1.0 - variation,
                high_factor=1.0 + variation,
                rank_corr_low=_rank_correlation(baseline_order, low_order),
                rank_corr_high=_rank_correlation(baseline_order, high_order),
                top_changed_low=(
                    bool(low_order) and low_order[0] != baseline_top
                ),
                top_changed_high=(
                    bool(high_order) and high_order[0] != baseline_top
                ),
            )
        )

    entries.sort(key=lambda e: e.max_disruption, reverse=True)

    # Plain-language summary (Phase 3.5 results-workspace sensitivity tab).
    top_ever_changed = any(
        e.top_changed_low or e.top_changed_high for e in entries
    )
    worst = entries[0].max_disruption if entries else 0.0
    if not top_ever_changed and worst < 0.05:
        summary = (
            f"This ranking is very robust — across a +/-{int(variation*100)}% "
            "change in any single economic weight, the order barely moves "
            "and the top animal never changes."
        )
    elif not top_ever_changed:
        summary = (
            f"This ranking is fairly robust — a +/-{int(variation*100)}% "
            "change in an economic weight shifts some positions, but the "
            "top animal stays the same."
        )
    else:
        summary = (
            "This ranking is sensitive — a plausible change in at least one "
            "economic weight is enough to change which animal ranks first. "
            "Treat close rankings with caution."
        )

    return SensitivityResult(
        entries=entries, baseline_top=baseline_top, summary=summary
    )
