"""
Breeding goal definition for osit-index.

The breeding goal (aggregate genotype, ``H``) is what the breeder wants to
improve: the economically weighted set of goal traits. It is the vector ``a``
of the selection-index equations.

Reference: NexGenIQ Phase 1 Section 2.2.1; Phase 3 Part 3A Section 1.1.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EconomicBasis(str, Enum):
    """The common denominator all economic weights in a goal must share.

    Mixing bases corrupts the index (Phase 1 Section 2.3.2), so a goal
    declares one basis and the engine enforces it.
    """

    PER_COW_EXPOSED = "per_cow_exposed"
    PER_CALF = "per_calf"
    PER_UNIT = "per_unit"


@dataclass
class GoalComponent:
    """One trait in the breeding goal and its economic weight.

    Attributes
    ----------
    trait_code:
        The goal trait (matches :data:`traits.TRAIT_REGISTRY`).
    economic_weight:
        Marginal economic value ``a_k`` — the change in profit per one-unit
        genetic improvement in this trait (Phase 1 Section 2.3). May be
        negative: e.g. mature cow weight in a maternal index. The engine
        never assumes "more is better".
    """

    trait_code: str
    economic_weight: float


@dataclass
class BreedingGoal:
    """A complete breeding goal: goal components on one economic basis.

    Attributes
    ----------
    name:
        Human-readable identifier (e.g. ``"Self-replacing herd, weaning"``).
    basis:
        The economic basis shared by every component.
    components:
        Ordered list of :class:`GoalComponent`. Order defines the trait
        ordering of the economic-weight vector ``a``.
    source:
        Provenance of the economic weights — ``"manual"``, ``"preset"`` or
        ``"simulation"`` — recorded for the reproducibility ledger.
    """

    name: str
    basis: EconomicBasis
    components: list[GoalComponent] = field(default_factory=list)
    source: str = "manual"

    @property
    def trait_codes(self) -> list[str]:
        """Ordered trait codes of the goal."""
        return [c.trait_code for c in self.components]

    @property
    def economic_weights(self) -> list[float]:
        """Ordered economic weights ``a``, aligned with :attr:`trait_codes`."""
        return [c.economic_weight for c in self.components]

    def __post_init__(self) -> None:
        codes = self.trait_codes
        if len(codes) != len(set(codes)):
            dupes = sorted({c for c in codes if codes.count(c) > 1})
            raise ValueError(
                f"Breeding goal {self.name!r} lists trait(s) more than "
                f"once: {', '.join(dupes)}."
            )
