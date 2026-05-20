"""
Multi-breed across-breed adjustment for osit-index.

EPDs from different breed associations are not directly comparable — each
association runs its own national evaluation on its own base (Phase 1
Section 1.6). The U.S. Meat Animal Research Center (USMARC), through the
Beef Improvement Federation, publishes annual adjustment factors that move a
within-breed EPD onto a common (Angus) base:

    EPD_adjusted = EPD_within_breed + AF(breed, trait, table_version)

Once every animal's EPDs are on the common base, animals of different breeds
can be ranked together.

This module applies that transformation as an explicit, reversible step and
records every factor used. The factor *values* themselves are reference data
(see :mod:`osit_index.data`) — this module is the mechanism.

Reference: NexGenIQ Phase 1 Section 1.6.1; Phase 3 Part 3B Section 2.3.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .animal import Animal, AnimalSet


@dataclass
class AdjustmentFactorTable:
    """A versioned table of USMARC/BIF across-breed adjustment factors.

    Attributes
    ----------
    version:
        Table version, recorded in the reproducibility ledger (e.g.
        ``"USMARC-2026"``).
    base_breed:
        The breed the factors adjust toward (Angus, by USMARC convention).
        The base breed always has a factor of 0 for every trait.
    factors:
        Mapping of ``(breed, trait_code)`` -> additive factor in the trait's
        units.
    """

    version: str
    base_breed: str = "Angus"
    factors: dict[tuple[str, str], float] = field(default_factory=dict)

    def factor(self, breed: str, trait_code: str) -> float | None:
        """Return the adjustment factor for ``(breed, trait_code)``.

        Returns 0.0 for the base breed (no adjustment needed). Returns
        ``None`` if the breed/trait pair has no published factor — the
        caller must then decide whether to refuse the run or accept a
        user-supplied factor (Phase 1 Section 1.6.1).
        """
        if breed == self.base_breed:
            return 0.0
        return self.factors.get((breed, trait_code))

    def covered_traits(self) -> set[str]:
        """Trait codes for which this table has at least one factor."""
        return {trait for (_breed, trait) in self.factors}

    def covered_breeds(self) -> set[str]:
        """Breeds for which this table has factors (plus the base breed)."""
        return {breed for (breed, _trait) in self.factors} | {self.base_breed}


@dataclass
class AdjustmentRecord:
    """A record of one applied adjustment, for the reproducibility ledger."""

    animal_id: str
    trait_code: str
    breed: str
    original_value: float
    factor: float
    adjusted_value: float


@dataclass
class AdjustmentResult:
    """The outcome of an across-breed adjustment pass.

    Attributes
    ----------
    animal_set:
        A new :class:`AnimalSet` with adjusted EPD values. The input set is
        never mutated — adjustment is a pure transformation.
    records:
        One :class:`AdjustmentRecord` per applied factor.
    table_version:
        The factor-table version used (``""`` if no adjustment was applied).
    applied:
        ``True`` if any adjustment was performed.
    """

    animal_set: AnimalSet
    records: list[AdjustmentRecord] = field(default_factory=list)
    table_version: str = ""
    applied: bool = False


def apply_across_breed_adjustment(
    animal_set: AnimalSet,
    trait_codes: list[str],
    table: AdjustmentFactorTable | None,
    *,
    native_multi_breed: bool = False,
    user_factors: dict[tuple[str, str], float] | None = None,
) -> AdjustmentResult:
    """Put every animal's EPDs on a common base for multi-breed comparison.

    The decision logic follows Phase 1 Section 1.6:

    * If the animal set is single-breed, or ``native_multi_breed`` is set
      (the EPDs already come from one multi-breed evaluation), no adjustment
      is applied and the set is returned unchanged.
    * Otherwise each EPD is shifted by its ``(breed, trait)`` factor from
      ``table``. A ``user_factors`` mapping supplies factors for pairs the
      published table does not cover.

    Parameters
    ----------
    animal_set:
        The candidate animals.
    trait_codes:
        The traits that will enter the index — only these are adjusted.
    table:
        The published adjustment-factor table. May be ``None`` only when no
        adjustment is required (single-breed or native multi-breed).
    native_multi_breed:
        Set ``True`` when all EPDs come from a single multi-breed evaluation
        (e.g. International Genetic Solutions). Adjustment is then skipped.
    user_factors:
        Optional user-supplied factors for ``(breed, trait)`` pairs missing
        from ``table``. Results that rely on these are the caller's to flag
        as user-derived.

    Returns
    -------
    AdjustmentResult
        The adjusted set, the per-factor records, and metadata.

    Raises
    ------
    ValueError
        If adjustment is required but no factor (published or user-supplied)
        exists for some ``(breed, trait)`` pair. The message names the
        missing pairs so the UI can explain the problem precisely.
    """
    user_factors = user_factors or {}

    # No adjustment needed: single breed, or one native multi-breed eval.
    if not animal_set.is_multi_breed or native_multi_breed:
        return AdjustmentResult(animal_set=animal_set, applied=False)

    if table is None:
        raise ValueError(
            "The animal set spans multiple breeds, so an across-breed "
            "adjustment factor table is required (or declare the data as a "
            "single native multi-breed evaluation)."
        )

    # Work on a deep copy — adjustment must not mutate the caller's data.
    adjusted = copy.deepcopy(animal_set)
    records: list[AdjustmentRecord] = []
    missing: list[tuple[str, str]] = []

    for animal in adjusted:
        for code in trait_codes:
            epd = animal.epd(code)
            if epd is None:
                continue  # missing EPDs are handled by the validation layer
            factor = table.factor(animal.breed, code)
            if factor is None:
                factor = user_factors.get((animal.breed, code))
            if factor is None:
                missing.append((animal.breed, code))
                continue
            original = epd.value
            epd.value = original + factor
            records.append(
                AdjustmentRecord(
                    animal_id=animal.animal_id,
                    trait_code=code,
                    breed=animal.breed,
                    original_value=original,
                    factor=factor,
                    adjusted_value=epd.value,
                )
            )

    if missing:
        unique = sorted(set(missing))
        pairs = ", ".join(f"{b}/{t}" for b, t in unique)
        raise ValueError(
            "No across-breed adjustment factor is available for these "
            f"breed/trait combinations: {pairs}. Supply a factor for each, "
            "or remove the affected trait from the index."
        )

    return AdjustmentResult(
        animal_set=adjusted,
        records=records,
        table_version=table.version,
        applied=True,
    )
