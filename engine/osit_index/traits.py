"""
Trait registry for osit-index.

A trait is a measurable characteristic with a published EPD. The registry is
deliberately *data*, not hard-coded logic (Phase 2 gap G9) — traits can be
extended without touching engine code, and the same engine generalises to
other species by supplying a different registry.

Each trait carries a stable code, a human-readable name, a biological
category (Phase 1 Section 1.2), units, and a `higher_is_better` hint used
only for UI presentation (the index math itself never assumes a direction —
economic weights, which may be negative, carry that information).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TraitCategory(str, Enum):
    """Biological grouping of traits (Phase 1 Section 1.2)."""

    GROWTH = "growth"
    MATERNAL = "maternal"
    CARCASS = "carcass"
    FERTILITY = "fertility"
    FEED_EFFICIENCY = "feed_efficiency"
    TEMPERAMENT = "temperament"
    HEALTH = "health"
    OTHER = "other"


@dataclass(frozen=True)
class Trait:
    """A single trait definition.

    Attributes
    ----------
    code:
        Stable short identifier (e.g. ``"WW"``). Used as the key everywhere
        EPDs, parameters and goal components are matched up.
    name:
        Human-readable name shown in the UI.
    category:
        Biological category.
    units:
        Units the EPD is expressed in (e.g. ``"lb"``).
    higher_is_better:
        UI hint only. ``True`` if, all else equal, a larger EPD is generally
        desirable. The index math does NOT use this — direction is carried by
        the (possibly negative) economic weight.
    is_threshold:
        ``True`` for traits whose observed phenotype is categorical but whose
        genetic liability is continuous (calving ease, stayability, heifer
        pregnancy). Their EPDs are accepted as published; the engine flags
        the linearity assumption (Phase 1 Section 1.2, Phase 3 Appendix A.4).
    breeds:
        If non-empty, the trait's EPD is published only by these breed
        associations, and the trait is offered only when the herd contains
        such breeds. PAP, for example, is published only by Angus (AAA) and
        Simmental (ASA). An empty tuple means the trait is breed-universal.
    description:
        Plain-language explanation surfaced in the help system.
    """

    code: str
    name: str
    category: TraitCategory
    units: str
    higher_is_better: bool = True
    is_threshold: bool = False
    breeds: tuple[str, ...] = ()
    description: str = ""


#: The built-in beef-cattle trait registry. Keyed by trait code.
TRAIT_REGISTRY: dict[str, Trait] = {
    t.code: t
    for t in [
        # --- Growth ---------------------------------------------------------
        Trait("BW", "Birth weight", TraitCategory.GROWTH, "lb",
              higher_is_better=False,
              description="Predicted birth weight of progeny. Lower birth "
                          "weight generally eases calving, but very low "
                          "values can cost growth."),
        Trait("WW", "Weaning weight", TraitCategory.GROWTH, "lb",
              description="Predicted weaning weight of progeny — a direct "
                          "measure of pre-weaning growth (the calf's own "
                          "genetics for growth)."),
        Trait("YW", "Yearling weight", TraitCategory.GROWTH, "lb",
              description="Predicted yearling weight of progeny, reflecting "
                          "growth through the post-weaning period."),
        Trait("PWG", "Post-weaning gain", TraitCategory.GROWTH, "lb",
              description="Predicted gain from weaning to yearling. Yearling "
                          "weight is approximately weaning weight plus this."),
        # --- Maternal -------------------------------------------------------
        Trait("MILK", "Maternal milk", TraitCategory.MATERNAL, "lb",
              description="The milk component of a daughter's calves' "
                          "weaning weight — expressed in pounds of calf "
                          "weaning weight, not literal milk yield."),
        Trait("MW", "Mature cow weight", TraitCategory.MATERNAL, "lb",
              higher_is_better=False,
              description="Predicted mature weight of daughters. Larger cows "
                          "eat more, so this often carries a negative "
                          "economic weight in maternal indexes."),
        Trait("STAY", "Stayability", TraitCategory.FERTILITY, "%",
              is_threshold=True,
              description="Probability a daughter remains productive in the "
                          "herd to a defined age — a longevity / sustained "
                          "fertility trait."),
        # --- Fertility ------------------------------------------------------
        Trait("CED", "Calving ease direct", TraitCategory.FERTILITY, "%",
              is_threshold=True,
              description="Probability a sire's calves are born unassisted "
                          "from first-calf heifers (the calf's own effect "
                          "on calving ease)."),
        Trait("CEM", "Calving ease maternal", TraitCategory.FERTILITY, "%",
              is_threshold=True,
              description="Probability a sire's daughters calve unassisted "
                          "as first-calf heifers (the daughter's effect on "
                          "calving ease)."),
        Trait("HP", "Heifer pregnancy", TraitCategory.FERTILITY, "%",
              is_threshold=True,
              description="Probability a sire's daughters conceive and are "
                          "pregnant as yearling heifers."),
        Trait("SC", "Scrotal circumference", TraitCategory.FERTILITY, "cm",
              description="Predicted scrotal circumference of sons — "
                          "genetically correlated with female fertility."),
        # --- Carcass --------------------------------------------------------
        Trait("CW", "Carcass weight", TraitCategory.CARCASS, "lb",
              description="Predicted hot carcass weight of progeny."),
        Trait("MARB", "Marbling", TraitCategory.CARCASS, "score",
              description="Predicted intramuscular fat (marbling) score — "
                          "the main driver of quality grade."),
        Trait("REA", "Ribeye area", TraitCategory.CARCASS, "sq in",
              description="Predicted ribeye (longissimus muscle) area — a "
                          "measure of red-meat yield."),
        Trait("FAT", "Backfat thickness", TraitCategory.CARCASS, "in",
              higher_is_better=False,
              description="Predicted external fat thickness over the ribeye. "
                          "Excess fat is trimmed and lowers yield grade."),
        # --- Feed efficiency ------------------------------------------------
        Trait("DMI", "Dry matter intake", TraitCategory.FEED_EFFICIENCY,
              "lb/day", higher_is_better=False,
              description="Predicted feed intake. Lower intake for the same "
                          "gain means a more efficient, cheaper-to-feed "
                          "animal."),
        Trait("RFI", "Residual feed intake", TraitCategory.FEED_EFFICIENCY,
              "lb/day", higher_is_better=False,
              description="Feed intake adjusted for body weight and gain — "
                          "a direct measure of feed efficiency. Lower (more "
                          "negative) is more efficient."),
        # --- Temperament ----------------------------------------------------
        Trait("DOC", "Docility", TraitCategory.TEMPERAMENT, "score",
              is_threshold=True,
              description="Predicted disposition of progeny. Calmer cattle "
                          "handle better and can perform better."),
        # --- Health ---------------------------------------------------------
        Trait("PAP", "Pulmonary arterial pressure", TraitCategory.HEALTH,
              "mmHg", higher_is_better=False,
              breeds=("Angus", "Red Angus", "Simmental"),
              description="Predicted pulmonary arterial pressure of progeny. "
                          "High PAP indicates susceptibility to high-altitude "
                          "(brisket / bovine pulmonary hypertension) disease; "
                          "lower is better. Published by AAA (Angus) and ASA "
                          "(Simmental); economically important only at "
                          "elevation. The breeding-goal weight scales with "
                          "the production scenario's elevation."),
        Trait("PAP_L", "Pulmonary arterial pressure (latent)",
              TraitCategory.HEALTH, "latent-z", higher_is_better=False,
              breeds=("Angus", "Red Angus", "Simmental"),
              description="A boundary-aware, latent-scale PAP phenotype. Raw "
                          "PAP is a practically bounded, measurement-error-"
                          "prone observation of an underlying physiological "
                          "state; mapping it through a logit transform onto "
                          "an unbounded latent scale removes the compression "
                          "near the practical bounds and recovers heritable "
                          "signal (latent-z h2 ~ 0.32 vs ~ 0.25 for raw PAP; "
                          "Markel et al.). Use this trait when your "
                          "evaluation publishes a latent-scale PAP EPD. It is "
                          "dimensionless: its economic value is dollars per "
                          "latent-z unit, not per mmHg."),
    ]
}


#: Trait codes whose EPD is published only by certain breed associations.
#: Derived from the registry so it stays in sync.
BREED_RESTRICTED_TRAITS: dict[str, tuple[str, ...]] = {
    code: t.breeds for code, t in TRAIT_REGISTRY.items() if t.breeds
}


def traits_available_for_breeds(breeds: set[str]) -> list[str]:
    """Return the trait codes usable for a herd of the given breeds.

    A breed-universal trait is always available. A breed-restricted trait
    (e.g. PAP) is available only when at least one of the herd's breeds
    publishes it. This is how the UI decides which EPDs to offer.
    """
    available: list[str] = []
    for code, trait in TRAIT_REGISTRY.items():
        if not trait.breeds or breeds & set(trait.breeds):
            available.append(code)
    return available


def get_trait(code: str) -> Trait:
    """Return the :class:`Trait` for ``code``.

    Raises
    ------
    KeyError
        If ``code`` is not in the registry. The message lists valid codes so
        the caller (and ultimately the UI) can give a helpful error.
    """
    try:
        return TRAIT_REGISTRY[code]
    except KeyError:
        valid = ", ".join(sorted(TRAIT_REGISTRY))
        raise KeyError(
            f"Unknown trait code {code!r}. Known traits: {valid}."
        ) from None
