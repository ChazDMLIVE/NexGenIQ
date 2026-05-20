"""
Plain-language ranking explanations for osit-index.

A signature NexGenIQ feature (Phase 3.5 Section 4.5.1): when a user looks at
a ranked animal, the interface explains *why* it ranks where it does, in a
sentence anyone can read — not an opaque index number. This module generates
that sentence from an :class:`index.AnimalScore`.

It is engine-side, not UI-side, so the explanation is consistent everywhere
the score appears (web, API, exported PDF) and is itself testable.
"""

from __future__ import annotations

from .index import AnimalScore, IndexResult
from .traits import TRAIT_REGISTRY


def _trait_name(code: str) -> str:
    """Human-readable trait name, falling back to the code."""
    trait = TRAIT_REGISTRY.get(code)
    return trait.name.lower() if trait else code


def explain_score(score: AnimalScore, result: IndexResult) -> str:
    """Return a plain-language explanation of one animal's ranking.

    The explanation names the traits that most help and most hurt the
    animal, framed relative to the rest of the field, in one or two
    sentences. Example output:

        "AAA-1842 ranks 1st of 42. It is carried mainly by strong calving
        ease and weaning weight; nothing meaningfully holds it back."

    Parameters
    ----------
    score:
        The animal to explain.
    result:
        The full :class:`IndexResult`, used to compare this animal's
        per-trait contributions against the field average.

    Returns
    -------
    str
        A complete, plain-language explanation sentence (or two).
    """
    n = len(result.scores)
    place = f"{_ordinal(score.rank)} of {n}"

    if not score.contributions:
        return f"{score.animal_id} ranks {place}."

    # Compare each trait's contribution with the field average for that
    # trait — a trait "helps" if this animal is above the field average.
    field_avg: dict[str, float] = {}
    for code in result.info_codes:
        vals = [s.contributions.get(code, 0.0) for s in result.scores]
        field_avg[code] = sum(vals) / len(vals) if vals else 0.0

    deltas = {
        code: score.contributions.get(code, 0.0) - field_avg.get(code, 0.0)
        for code in result.info_codes
    }
    helps = sorted(
        (c for c in deltas if deltas[c] > 0), key=lambda c: -deltas[c]
    )
    hurts = sorted((c for c in deltas if deltas[c] < 0), key=lambda c: deltas[c])

    parts = [f"{score.animal_id} ranks {place}."]

    if helps:
        top_help = [_trait_name(c) for c in helps[:2]]
        verb = "is carried mainly by" if score.rank <= n / 2 else "is helped by"
        parts.append(f"It {verb} {_join(top_help)}")
        if hurts and deltas[hurts[0]] < -0.5 * abs(deltas[helps[0]]):
            parts[-1] += (
                f"; its weaker {_trait_name(hurts[0])} holds it back."
            )
        else:
            parts[-1] += "."
    elif hurts:
        top_hurt = [_trait_name(c) for c in hurts[:2]]
        parts.append(
            f"It ranks low mainly because of weaker {_join(top_hurt)}."
        )

    if score.is_partial:
        parts.append(
            "Note: some EPDs were missing and treated as breed average, so "
            "this position is approximate."
        )
    elif score.std_error is not None and n > 1:
        spread = max(s.index_value for s in result.scores) - min(
            s.index_value for s in result.scores
        )
        if spread > 0 and score.std_error > 0.25 * spread:
            parts.append(
                "Its index value is fairly uncertain — the EPDs behind it "
                "have low accuracy."
            )

    return " ".join(parts)


def _ordinal(n: int) -> str:
    """Return ``n`` as an ordinal string: 1 -> '1st', 2 -> '2nd', etc."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _join(items: list[str]) -> str:
    """Join a short list into readable prose: [a] -> 'a'; [a,b] -> 'a and b'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"
