"""
Genetic model for the osit-sim herd simulation.

Supplies the per-trait genetic parameters, the breed additive effects, and
the F1 heterosis values that the herd simulation uses to generate each
animal's genetic merit and phenotype.

The breed additive effects for the growth and carcass traits are taken
from the USMARC across-breed EPD adjustment factors (the same sourced
values the index engine uses); the remaining per-trait deviations and the
F1 heterosis values are representative figures consistent with those
estimates and with the published heterosis literature. A researcher can
override any of them with population-specific estimates.

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
    # --- Growth -----------------------------------------------------------
    "BW":   TraitGenetics("BW",   85.0,  4.0,  0.40),
    "WW":   TraitGenetics("WW",  545.0, 22.0,  0.25,
                          has_maternal=True, maternal_sd=14.0),
    "YW":   TraitGenetics("YW",  850.0, 35.0,  0.40),
    "PWG":  TraitGenetics("PWG", 305.0, 20.0,  0.30),
    # --- Maternal ---------------------------------------------------------
    "MILK": TraitGenetics("MILK", 0.0,  14.0,  0.20),
    "MW":   TraitGenetics("MW", 1300.0, 70.0,  0.50),
    # --- Fertility / longevity -------------------------------------------
    "CED":  TraitGenetics("CED", 92.0,   6.0,  0.22),
    "CEM":  TraitGenetics("CEM", 92.0,   5.0,  0.18),
    "HP":   TraitGenetics("HP",  90.0,   7.0,  0.13),
    "SC":   TraitGenetics("SC",  37.0,   1.1,  0.45),
    "STAY": TraitGenetics("STAY", 55.0,  8.0,  0.12),
    # --- Carcass ----------------------------------------------------------
    "CW":   TraitGenetics("CW",  800.0, 30.0,  0.40),
    "MARB": TraitGenetics("MARB", 5.0,   0.55, 0.38),
    "REA":  TraitGenetics("REA", 13.0,   0.60, 0.40),
    "FAT":  TraitGenetics("FAT",  0.50,  0.07, 0.35),
    # --- Feed efficiency --------------------------------------------------
    "DMI":  TraitGenetics("DMI", 22.0,   1.4,  0.35),
    "RFI":  TraitGenetics("RFI",  0.0,   0.55, 0.40),
    # --- Temperament ------------------------------------------------------
    "DOC":  TraitGenetics("DOC", 22.0,   3.0,  0.25),
    # --- Health -----------------------------------------------------------
    # PAP: pulmonary arterial pressure, mmHg. Mean ~41 mmHg; an animal
    # above ~49 mmHg is considered high-risk for high-altitude disease.
    # Moderately heritable (literature estimates 0.20-0.35).
    "PAP":  TraitGenetics("PAP", 41.0,   3.2,  0.30),
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
#
# The BW, WW, YW, MILK, CW, MARB, REA and FAT deviations are taken from the
# USMARC across-breed EPD adjustment factors (Kuehn and Thallman; the same
# values the index engine uses for across-breed adjustment) - they are the
# best-available, regularly-updated estimates of beef breed differences on
# an Angus base. The remaining deviations (PWG, MW, CED, CEM, DMI, DOC) are
# representative figures consistent with those values and with breed
# reputation, used only by the herd simulation; a researcher should
# override them with population-specific estimates where available.
#
# PAP: only Angus and Simmental have an official PAP evaluation. Simmental
# carries a small positive (worse) illustrative PAP deviation; every other
# breed is simply absent from the PAP key and contributes 0, and PAP is
# only simulated when the herd contains a PAP-evaluated breed.
# ---------------------------------------------------------------------------
_BREED_EFFECTS: dict[str, dict[str, float]] = {
    "Angus":    {},  # the base breed - all zero
    "Hereford": {
        "BW": 0.8, "WW": -4.2, "YW": -8.6, "MILK": -18.0,
        "PWG": -5.0, "MW": -40.0, "CW": -23.3, "MARB": -0.20,
        "REA": -0.04, "FAT": 0.011, "CED": -1.0, "CEM": -2.0,
        "DMI": -0.6, "DOC": -1.5,
    },
    "Red Angus": {
        "BW": -0.2, "WW": -3.4, "YW": -5.5, "MILK": 1.5,
        "PWG": -2.0, "MW": -15.0, "CW": -4.0, "MARB": -0.10,
        "REA": -0.05, "FAT": 0.005, "CED": 0.5, "CEM": 1.0,
        "DMI": -0.2, "DOC": 0.5,
    },
    "Simmental": {
        "BW": 3.6, "WW": 16.8, "YW": 21.9, "MILK": 13.6,
        "PWG": 6.0, "MW": 60.0, "CW": 5.5, "MARB": -0.62,
        "REA": 0.55, "FAT": -0.103, "CED": -4.0, "CEM": -3.0,
        "DMI": 0.9, "DOC": -2.5, "PAP": 1.5,
    },
    "Charolais": {
        "BW": 5.5, "WW": 20.3, "YW": 21.4, "MILK": -0.5,
        "PWG": 6.0, "MW": 75.0, "CW": 11.6, "MARB": -0.84,
        "REA": 0.79, "FAT": -0.166, "CED": -7.0, "CEM": -4.0,
        "DMI": 1.1, "DOC": -3.0,
    },
    "Gelbvieh": {
        "BW": 2.9, "WW": -8.6, "YW": -15.9, "MILK": 6.0,
        "PWG": -3.0, "MW": 25.0, "CW": -17.5, "MARB": -0.44,
        "REA": 0.62, "FAT": -0.088, "CED": -3.0, "CEM": -2.0,
        "DMI": 0.4, "DOC": -1.5,
    },
    "Limousin": {
        "BW": 1.7, "WW": -3.9, "YW": -14.6, "MILK": -8.9,
        "PWG": -4.0, "MW": 15.0, "CW": -11.5, "MARB": -0.22,
        "REA": 0.62, "FAT": -0.062, "CED": -2.0, "CEM": -3.0,
        "DMI": 0.1, "DOC": -3.5,
    },
    "Shorthorn": {
        "BW": 4.0, "WW": -21.9, "YW": -20.1, "MILK": 0.2,
        "PWG": -3.0, "MW": -10.0, "CW": -7.3, "MARB": -0.03,
        "REA": 0.29, "FAT": -0.027, "CED": -1.0, "CEM": -1.0,
        "DMI": -0.3, "DOC": 0.0,
    },
    "Salers": {
        "BW": 2.3, "WW": -9.4, "YW": -14.7, "MILK": 3.8,
        "PWG": -3.0, "MW": 10.0, "CW": -21.2, "MARB": -0.15,
        "REA": 0.45, "FAT": -0.064, "CED": -2.0, "CEM": -1.0,
        "DMI": 0.2, "DOC": -1.0,
    },
    "Maine-Anjou": {
        "BW": 1.6, "WW": -27.2, "YW": -34.5, "MILK": -6.4,
        "PWG": -5.0, "MW": 35.0, "CW": -35.8, "MARB": -0.45,
        "REA": 0.85, "FAT": -0.146, "CED": -2.0, "CEM": -3.0,
        "DMI": 0.5, "DOC": -2.0,
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
    "PWG": 8.0,
    "MW": 30.0,
    "CW": 14.0,
    "CED": 2.0,
    "CEM": 2.5,
    "STAY": 4.0,
    "HP": 3.5,
    "SC": 0.5,
    "DOC": 0.8,
    # PAP shows modest favourable heterosis (lower pressure in crosses).
    "PAP": -1.0,
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
