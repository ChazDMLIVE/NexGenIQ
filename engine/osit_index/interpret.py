"""
Whole-result interpretation for osit-index.

Where :mod:`explain` explains one animal's ranking, this module interprets
the *whole* index result: a plain-language, producer-facing reading of what
the ranking means and what to do with it. It answers the questions a
producer actually has - "which animals do I keep?", "how confident can I
be?", "what is this index rewarding?" - in language anyone can read.

The interpretation is layered (NexGenIQ Phase 3.5): a one-line headline and
a short readout anyone can act on, plus a list of deeper detail points for
a user who wants the full reasoning. It is rule-based and deterministic -
built only from the result's own numbers - so it is reproducible, always
available, and itself testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .index import IndexResult, IndexMode
from .traits import TRAIT_REGISTRY


@dataclass
class ResultInterpretation:
    """A layered plain-language interpretation of an index result.

    Attributes
    ----------
    headline:
        A single sentence: the one thing to take away.
    readout:
        A short plain-language paragraph (2-4 sentences) a producer can
        act on without opening anything further.
    detail:
        A list of deeper explanation points, surfaced when the user
        expands the interpretation.
    cautions:
        Plain-language warnings the user should weigh before acting
        (uncertainty, approximate results, excluded animals).
    disclaimer:
        A standing notice that the interpretation is informational only -
        a decision-support output, not a recommendation to take any
        particular action.
    """

    headline: str = ""
    readout: str = ""
    detail: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    disclaimer: str = (
        "This interpretation is informational only. NexGenIQ describes "
        "what the analysis shows; it does not recommend that you select, "
        "cull, buy, or sell any animal. Selection and culling decisions "
        "are yours, and should weigh factors beyond this analysis - "
        "structure, health, temperament, price, and your own goals."
    )


def _trait_name(code: str) -> str:
    """Human-readable trait name, falling back to the code."""
    trait = TRAIT_REGISTRY.get(code)
    return trait.name.lower() if trait else code


def _join(items: list[str]) -> str:
    """Join a short list into readable prose."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _suggested_keep(n: int) -> int:
    """A sensible default number of animals to select from a field of n.

    Roughly the top quarter, bounded so the suggestion is never zero and
    never the whole field.
    """
    if n <= 2:
        return 1
    return max(1, min(n - 1, round(n * 0.25)))


def interpret_index_result(result: IndexResult) -> ResultInterpretation:
    """Interpret a whole index result in plain, producer-facing language.

    Parameters
    ----------
    result:
        The :class:`IndexResult` to interpret.

    Returns
    -------
    ResultInterpretation
        A layered interpretation: headline, readout, detail, cautions.
    """
    interp = ResultInterpretation()
    scores = result.scores
    n = len(scores)

    if n == 0:
        interp.headline = "No animals were ranked."
        interp.readout = (
            "The index could not rank any animals. Check the Checks panel "
            "for what needs fixing - usually a missing trait or an input "
            "problem."
        )
        return interp

    # --- what the index is rewarding -------------------------------------
    # The biggest-magnitude weights are what this index emphasises.
    weights = result.weights or {}
    ranked_traits = sorted(
        weights, key=lambda c: abs(weights[c]), reverse=True
    )
    emphasised = [_trait_name(c) for c in ranked_traits[:3]]

    top = scores[0]
    keep = _suggested_keep(n)

    # --- headline --------------------------------------------------------
    interp.headline = (
        f"{top.animal_id} is your top-ranked animal of {n}."
    )

    # --- readout ---------------------------------------------------------
    readout_parts: list[str] = []
    readout_parts.append(
        f"NexGenIQ ranked {n} animal{'s' if n != 1 else ''} on a single "
        f"index value that combines their EPDs by what each trait is "
        f"worth to your operation. A higher index value is better."
    )
    if emphasised:
        readout_parts.append(
            f"This index rewards {_join(emphasised)} most heavily, so the "
            f"animals at the top are the ones that best combine those "
            f"traits."
        )
    readout_parts.append(
        f"On this goal, the highest-ranked animals are the top {keep} "
        f"- down to {scores[keep - 1].animal_id}. This is a description "
        f"of how the animals compare on the index, not a recommendation "
        f"to keep or cull any of them: the ranking is one input to your "
        f"decision, and animals close together in index value are close "
        f"in estimated merit."
    )
    interp.readout = " ".join(readout_parts)

    # --- detail ----------------------------------------------------------
    spread = (
        scores[0].index_value - scores[-1].index_value if n > 1 else 0.0
    )
    interp.detail.append(
        f"The index value is a dollar-denominated estimate of each "
        f"animal's breeding merit for your goal. {top.animal_id} leads "
        f"at {top.index_value:.1f}; the field spans {spread:.1f} index "
        f"points from top to bottom."
    )
    if emphasised and weights:
        signed = []
        for c in ranked_traits[:3]:
            direction = "more" if weights[c] >= 0 else "less"
            signed.append(f"{_trait_name(c)} (rewarding {direction})")
        interp.detail.append(
            f"In order of influence, the index weights: {_join(signed)}. "
            f"A trait with a larger weight moves the ranking more."
        )
    if result.mode is IndexMode.BLUP_INDEX:
        interp.detail.append(
            "This run used the accuracy-adjusted index, which down-weights "
            "EPDs measured with low accuracy - so a high-accuracy animal "
            "is favoured over an equally-promising but unproven one."
        )
    else:
        interp.detail.append(
            "This run used the standard economic-weight index: each EPD "
            "is weighted purely by its economic value. If your animals "
            "vary a lot in EPD accuracy, the accuracy-adjusted index mode "
            "accounts for that."
        )
    # How tightly the field is bunched - decision-relevant.
    if n > 2 and spread > 0:
        gap_top = scores[0].index_value - scores[1].index_value
        if gap_top < 0.05 * spread:
            interp.detail.append(
                "Your top animals are very close in index value. The "
                "ranking among them is not a strong distinction - weigh "
                "other factors (price, structure, temperament) freely."
            )
        elif gap_top > 0.25 * spread:
            interp.detail.append(
                f"{top.animal_id} stands clearly ahead of the rest - a "
                f"decisive lead, not a narrow one."
            )

    # --- cautions --------------------------------------------------------
    partial = [s.animal_id for s in scores if s.is_partial]
    if partial:
        shown = ", ".join(partial[:5])
        more = "" if len(partial) <= 5 else f" (and {len(partial) - 5} more)"
        interp.cautions.append(
            f"{len(partial)} animal{'s' if len(partial) != 1 else ''} had "
            f"missing EPDs filled with a breed average ({shown}{more}); "
            f"their positions are approximate."
        )
    if result.excluded:
        shown = ", ".join(result.excluded[:5])
        more = (
            "" if len(result.excluded) <= 5
            else f" (and {len(result.excluded) - 5} more)"
        )
        interp.cautions.append(
            f"{len(result.excluded)} animal"
            f"{'s' if len(result.excluded) != 1 else ''} could not be "
            f"ranked and were left out ({shown}{more}) - usually a missing "
            f"trait. Add the missing EPDs to include them."
        )
    # Uncertainty: any animal whose CI is wide relative to the field.
    if n > 1 and spread > 0:
        uncertain = [
            s for s in scores
            if s.std_error is not None and s.std_error > 0.25 * spread
        ]
        if uncertain:
            interp.cautions.append(
                f"{len(uncertain)} animal"
                f"{'s' if len(uncertain) != 1 else ''} have a wide "
                f"confidence range - their EPDs have low accuracy, so "
                f"their exact rank could shift as more data accrue. "
                f"Be cautious comparing them on small index differences."
            )
    # Surface any validation warnings in plain language.
    warn_count = sum(
        1 for i in result.validation.issues
        if i.severity.value == "warn"
    )
    if warn_count:
        interp.cautions.append(
            f"The Checks panel has {warn_count} "
            f"warning{'s' if warn_count != 1 else ''} worth reading "
            f"before you act on this ranking."
        )

    return interp
