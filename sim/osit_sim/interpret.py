"""
Whole-result interpretation for osit-sim.

Interprets the output of an MEV derivation - the vector of derived economic
values - in plain, producer-facing language. It answers the questions a
producer has after running the herd simulation: "what do these numbers
mean?", "which traits matter most for my operation?", "how do I use them?".

The interpretation is layered (NexGenIQ Phase 3.5): a one-line headline and
a short readout anyone can act on, plus deeper detail points. It is
rule-based and deterministic - built only from the result's own numbers -
so it is reproducible, always available, and itself testable.

It carries a standing disclaimer: the interpretation is decision-support
information, not a recommendation to take any particular action.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .mev import MevResult

# Readable names for the trait codes the simulation can return.
_TRAIT_NAMES: dict[str, str] = {
    "BW": "birth weight",
    "WW": "weaning weight",
    "YW": "yearling weight",
    "PWG": "post-weaning gain",
    "MILK": "maternal milk",
    "MW": "mature cow weight",
    "CED": "calving ease direct",
    "CEM": "calving ease maternal",
    "HP": "heifer pregnancy",
    "SC": "scrotal circumference",
    "STAY": "stayability",
    "CW": "carcass weight",
    "MARB": "marbling",
    "REA": "ribeye area",
    "FAT": "backfat thickness",
    "DMI": "dry matter intake",
    "RFI": "residual feed intake",
    "DOC": "docility",
    "PAP": "pulmonary arterial pressure",
    "PAP_L": "latent pulmonary arterial pressure",
}


@dataclass
class MevInterpretation:
    """A layered plain-language interpretation of an MEV-derivation result.

    Attributes
    ----------
    headline:
        A single sentence: the one thing to take away.
    readout:
        A short plain-language paragraph a producer can act on.
    detail:
        Deeper explanation points, surfaced when the user expands.
    cautions:
        Plain-language warnings (imprecise estimates, etc.).
    disclaimer:
        A standing notice that the interpretation is informational only -
        not a recommendation to take any particular action.
    """

    headline: str = ""
    readout: str = ""
    detail: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    disclaimer: str = (
        "This interpretation is informational only. NexGenIQ describes "
        "what the simulation produced; it does not recommend a particular "
        "breeding goal or selection decision. The economic values are a "
        "modelled estimate for the operation you described - use them as "
        "one input alongside your own judgement and goals."
    )


def _name(code: str) -> str:
    """Human-readable trait name, falling back to the code."""
    return _TRAIT_NAMES.get(code, code)


def _join(items: list[str]) -> str:
    """Join a short list into readable prose."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def interpret_mev_result(result: MevResult) -> MevInterpretation:
    """Interpret an MEV-derivation result in plain, producer-facing language.

    Parameters
    ----------
    result:
        The :class:`mev.MevResult` to interpret.

    Returns
    -------
    MevInterpretation
        A layered interpretation: headline, readout, detail, cautions.
    """
    interp = MevInterpretation()
    mevs = result.mevs

    if not mevs:
        interp.headline = "No economic values were derived."
        interp.readout = (
            "The simulation did not return any economic values. Check the "
            "production-system and economic inputs and try again."
        )
        return interp

    # MEVs arrive ordered by descending absolute value - most important
    # trait first.
    most = mevs[0]
    pos = [m for m in mevs if m.mev > 0]
    neg = [m for m in mevs if m.mev < 0]

    # --- headline --------------------------------------------------------
    interp.headline = (
        f"For the operation you described, {_name(most.trait_code)} is "
        f"the trait with the most economic value at stake."
    )

    # --- readout ---------------------------------------------------------
    readout_parts: list[str] = []
    readout_parts.append(
        f"NexGenIQ simulated your operation and worked out what a one-unit "
        f"genetic improvement in each trait is worth - its economic value, "
        f"in dollars per cow per year. {len(mevs)} traits were valued."
    )
    top_names = [_name(m.trait_code) for m in mevs[:3]]
    readout_parts.append(
        f"The traits carrying the most economic value here are "
        f"{_join(top_names)}. A trait with a larger value (positive or "
        f"negative) should weigh more heavily in a breeding goal for this "
        f"operation."
    )
    readout_parts.append(
        "These values are a description of your modelled operation, not "
        "advice on what to select for. Carry them into the Index Builder "
        "to rank animals, or adjust the inputs and re-run to see how the "
        "values respond."
    )
    interp.readout = " ".join(readout_parts)

    # --- detail ----------------------------------------------------------
    interp.detail.append(
        f"Each economic value is the change in whole-herd profit, per cow "
        f"per year, from a one-unit genetic improvement in that trait. "
        f"{_name(most.trait_code)} leads at "
        f"{most.mev:+.2f} per {most.units}."
    )
    if pos:
        interp.detail.append(
            f"Traits with a positive value raise profit as they increase: "
            f"{_join([_name(m.trait_code) for m in pos[:4]])}"
            f"{' and others' if len(pos) > 4 else ''}."
        )
    if neg:
        interp.detail.append(
            f"Traits with a negative value cost you as they increase - "
            f"selection should favour lower values for these: "
            f"{_join([_name(m.trait_code) for m in neg[:4]])}"
            f"{' and others' if len(neg) > 4 else ''}."
        )
    interp.detail.append(
        f"The values were averaged over {result.replicates} independently "
        f"simulated herd{'s' if result.replicates != 1 else ''} sharing "
        f"common random numbers, which isolates the effect of each trait "
        f"from simulation noise. The baseline herd returned about "
        f"${result.baseline_profit:,.0f} a year."
    )
    interp.detail.append(
        "An economic value specific to your operation is the point of the "
        "simulation: the same trait can be worth very different amounts "
        "under different herd sizes, sale endpoints, costs, and elevation."
    )

    # --- cautions --------------------------------------------------------
    imprecise = [m for m in mevs if not m.is_precise]
    if imprecise:
        names = _join([_name(m.trait_code) for m in imprecise[:4]])
        interp.cautions.append(
            f"{len(imprecise)} economic value"
            f"{'s are' if len(imprecise) != 1 else ' is'} imprecise "
            f"({names}{' and others' if len(imprecise) > 4 else ''}) - the "
            f"Monte-Carlo error is large relative to the value. Re-run "
            f"with more replicate herds for a tighter estimate before "
            f"relying on those traits."
        )
    for w in result.warnings:
        interp.cautions.append(w)

    return interp
