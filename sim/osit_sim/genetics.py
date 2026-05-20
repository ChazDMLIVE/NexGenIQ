"""
Genetic model for the osit-sim herd simulation.

Supplies the per-trait genetic parameters, the breed additive effects, and
the F1 heterosis values that the herd simulation uses to generate each
animal's genetic merit and phenotype.

The breed-effect and heterosis values here are illustrative figures of the
structure and rough magnitude of the USMARC germplasm-evaluation estimates
(Phase 1 Section 1.6.1) — they let the engine run end to end and are
clearly labelled as illustrative. A production deployment loads versioned
official estimates.

Reference: NexGenIQ Phase 3 Part 3B Section 2.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .inputs import SIMULATED_TRAITS


@dataclass
class TraitGenetics:
    """Genetic parameters for one simulated trait.

    Attributes
    ----------
    code:
        Trait code (a key of :data:`inputs.SIMULATED_TRAITS`).
    mean:
        The phenotypic mean of the founding cow herd, in the trait's units.
    genetic_sd:
        Additive genetic standard deviation.
    heritability:
        Narrow-sense heritability — the additive share of phenotypic
        variance. With the genetic SD this also fixes the residual SD.
    has_maternal:
        ``True`` for traits with a maternal genetic component (e.g. WW,
        whose expression depends on the dam's milk as well as the calf's
        own growth genes).
    maternal_sd:
        Additive genetic SD of the maternal component, if any.
    """

    code: str
    mean: float
    genetic_sd: float
    heritability: float
    has_maternal: bool = False
    maternal_sd: float = 0.0

    @property
    def residual_sd(self) -> float:
        """Residual (non-additive) standard deviation.

        Derived from the phenotypic variance implied by the additive SD
        and the heritability: ``sigma_P^2 = sigma_A^2 / h^2`` and
        ``sigma_E^2 = sigma_P^2 - sigma_A^2``.
        """
        phenotypic_var = self.genetic_sd ** 2 / self.heritability
        residual_var = phenotypic_var - self.genetic_sd ** 2
        return residual_var ** 0.5


#: Default per-trait genetics for a commercial herd. Means are typical
#: commercial values; SDs and heritabilities are literature consensus
#: figures (consistent with the osit-index parameter library).
_DEFAULT_GENETICS: dict[str, TraitGenetics] = {
    "BW":   TraitGenetics("BW",   85.0,  4.0,  0.40),
    "WW":   TraitGenetics("WW",  545.0, 22.0,  0.25,
                          has_maternal=True, maternal_sd=14.0),
    "MILK": TraitGenetics("MILK", 0.0,  14.0,  0.20),
    "YW":   TraitGenetics("YW",  850.0, 35.0,  0.40),
    "MW":   TraitGenetics("MW", 1300.0, 70.0,  0.50),
    "CW":   TraitGenetics("CW",  800.0, 30.0,  0.40),
    "MARB": TraitGenetics("MARB", 5.0,   0.55, 0.38),
    "REA":  TraitGenetics("REA", 13.0,   0.60, 0.40),
    "FAT":  TraitGenetics("FAT",  0.50,  0.07, 0.35),
    "CED":  TraitGenetics("CED", 92.0,   6.0,  0.22),
    "STAY": TraitGenetics("STAY", 55.0,  8.0,  0.12),
    "HP":   TraitGenetics("HP",  90.0,   7.0,  0.13),
    "DMI":  TraitGenetics("DMI", 22.0,   1.4,  0.35),
}


def default_herd_genetics() -> dict[str, TraitGenetics]:
    """Return a fresh copy of the default per-trait herd genetics."""
    return {
        code: TraitGenetics(
            g.code, g.mean, g.genetic_sd, g.heritability,
            g.has_maternal, g.maternal_sd,
        )
        for code, g in _DEFAULT_GENETICS.items()
    }


# ---------------------------------------------------------------------------
# Breed additive effects, expressed as deviations from an Angus base.
# Illustrative figures of the structure of USMARC germplasm estimates.
# ---------------------------------------------------------------------------
_BREED_EFFECTS: dict[str, dict[str, float]] = {
    "Angus":    {},  # the base breed — all zero
    "Hereford": {
        "BW": 4.0, "WW": -20.0, "MILK": -18.0, "YW": -28.0,
        "MW": -40.0, "CW": -55.0, "MARB": -0.9, "REA": -0.3,
        "CED": -3.0,
    },
    "Simmental": {
        "BW": 5.0, "WW": 18.0, "MILK": 8.0, "YW": 22.0,
        "MW": 60.0, "CW": 35.0, "MARB": -1.1, "REA": 0.9,
        "CED": -5.0,
    },
    "Red Angus": {
        "BW": 0.0, "WW": -8.0, "MILK": 4.0, "YW": -10.0,
        "MW": -20.0, "CW": -6.0, "MARB": -0.2, "REA": -0.1,
        "CED": 1.0,
    },
    "Charolais": {
        "BW": 7.0, "WW": 22.0, "MILK": -6.0, "YW": 30.0,
        "MW": 75.0, "CW": 50.0, "MARB": -1.4, "REA": 1.2,
        "CED": -8.0,
    },
}


def breed_effect(breed: str, trait: str) -> float:
    """Return the additive breed effect of ``breed`` for ``trait``.

    Zero for the Angus base, and zero for any breed/trait pair without a
    listed effect.
    """
    return _BREED_EFFECTS.get(breed, {}).get(trait, 0.0)


# ---------------------------------------------------------------------------
# F1 heterosis. Heterosis is largest for lowly heritable fitness and
# maternal traits and is expressed in proportion to breed heterozygosity
# (Phase 1 Section 1.6.3). Values here are the full-F1 (100% heterozygosity)
# effect, illustrative in magnitude.
# ---------------------------------------------------------------------------
_F1_HETEROSIS: dict[str, float] = {
    "BW": 1.5,
    "WW": 18.0,
    "MILK": 8.0,
    "YW": 26.0,
    "MW": 30.0,
    "CW": 14.0,
    "CED": 2.0,
    "STAY": 4.0,
    "HP": 3.5,
}


def heterosis_value(trait: str, heterozygosity: float) -> float:
    """Return the heterosis contribution for a trait at a heterozygosity.

    Parameters
    ----------
    trait:
        The trait code.
    heterozygosity:
        The animal's breed heterozygosity in [0, 1] — 0 for a purebred,
        1 for an F1 cross of two unrelated breeds. Retained heterosis in
        later crosses falls between.

    Returns
    -------
    float
        The heterosis effect, scaled linearly by heterozygosity.
    """
    return _F1_HETEROSIS.get(trait, 0.0) * heterozygosity
