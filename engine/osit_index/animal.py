"""
Candidate animals for osit-index.

An :class:`Animal` is a selection candidate — a bull, semen source, heifer or
embryo the user is choosing between — carrying its EPDs and their accuracies.

The engine is strict about provenance: every EPD records the evaluation it
came from, because EPDs from different national evaluations are not directly
comparable (Phase 1 Section 1.6). This is what allows the across-breed
adjustment step to be applied — or refused — correctly.

Reference: NexGenIQ Phase 3 Part 3A Section 1.3.1, Part 3C Section 3.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EpdScale(str, Enum):
    """Whether a value is reported on the EPD scale or the EBV scale.

    EPD = EBV / 2 (Phase 1 Section 1.1). Most North American beef
    associations publish EPDs; some evaluations publish EBVs. Mixing the two
    silently halves or doubles every prediction, so the scale is explicit.
    """

    EPD = "EPD"
    EBV = "EBV"


@dataclass
class EpdValue:
    """A single trait prediction for an animal.

    Attributes
    ----------
    trait_code:
        The trait predicted.
    value:
        The predicted value, in the trait's units, on the scale given by
        :attr:`scale`.
    bif_accuracy:
        BIF accuracy of the prediction, in [0, 1] (Phase 1 Section 1.4).
        ``None`` if unknown — the engine then treats the prediction as
        having an accuracy of 0 for uncertainty purposes and warns.
    scale:
        EPD or EBV. The engine normalises everything to the EPD scale
        internally.
    """

    trait_code: str
    value: float
    bif_accuracy: float | None = None
    scale: EpdScale = EpdScale.EPD

    def value_as_epd(self) -> float:
        """Return the value on the EPD (progeny-difference) scale.

        EBV-scale values are halved; EPD-scale values are returned as-is.
        """
        if self.scale is EpdScale.EBV:
            return self.value / 2.0
        return self.value


@dataclass
class Animal:
    """A candidate animal.

    Attributes
    ----------
    animal_id:
        Stable identifier (registration number, tag, etc.).
    breed:
        Breed code, used for across-breed adjustment (e.g. ``"Angus"``).
    epds:
        Mapping of trait code -> :class:`EpdValue`.
    evaluation_id:
        Identifier of the national evaluation these EPDs came from
        (association + base year + provider). Animals with different
        evaluation ids cannot be compared without across-breed adjustment.
    sex:
        Optional sex code, carried for reporting.
    """

    animal_id: str
    breed: str
    epds: dict[str, EpdValue] = field(default_factory=dict)
    evaluation_id: str = ""
    sex: str = ""

    def epd(self, trait_code: str) -> EpdValue | None:
        """Return the :class:`EpdValue` for ``trait_code``, or ``None``."""
        return self.epds.get(trait_code)

    def has_traits(self, codes: list[str]) -> list[str]:
        """Return the subset of ``codes`` for which this animal has no EPD."""
        return [c for c in codes if c not in self.epds]


@dataclass
class AnimalSet:
    """A collection of candidate animals to be ranked together.

    Attributes
    ----------
    animals:
        The candidate animals.
    name:
        Optional human-readable label (e.g. a sale catalogue name).
    """

    animals: list[Animal] = field(default_factory=list)
    name: str = ""

    def __len__(self) -> int:
        return len(self.animals)

    def __iter__(self):
        return iter(self.animals)

    @property
    def breeds(self) -> set[str]:
        """Distinct breeds present in the set."""
        return {a.breed for a in self.animals}

    @property
    def evaluation_ids(self) -> set[str]:
        """Distinct evaluation identities present in the set."""
        return {a.evaluation_id for a in self.animals}

    @property
    def is_multi_breed(self) -> bool:
        """True if the set spans more than one breed."""
        return len(self.breeds) > 1
