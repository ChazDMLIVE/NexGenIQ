"""
Phenotype-to-breeding-value conversion for osit-index.

Many producers do not have EPDs but do have raw, age-standardized
performance records — actual weaning weights, yearling weights, scrotal
circumferences and so on — measured on their own animals. This module
lets those producers use the Index Builder.

A raw phenotype is not a breeding value: a heavy calf may be heavy
because of good genes, or an easy contemporary group, or its dam. To
rank animals on heritable merit the phenotypes must first be turned into
estimated breeding values. With no pedigree and no progeny the defensible
method is **mass selection** — selection on adjusted own performance:

1. Adjust each phenotype to a deviation from its *contemporary-group*
   mean (the group of animals managed and measured together). This
   removes the group-level environmental effect, so a good animal in a
   hard group is not penalised against a poor animal in an easy group.

2. Convert the within-group deviation to an estimated breeding value::

       EBV = h2 * (phenotype - contemporary_group_mean)

   This is the standard own-performance predictor: the heritability is
   the regression of breeding value on phenotypic deviation.

3. Assign a BIF accuracy for a single own-performance record::

       accuracy = sqrt(h2)

   This is genuinely lower than a published EPD's accuracy, and that is
   correct — the index engine propagates accuracy into every confidence
   interval, so a phenotype-derived animal honestly shows wider bands
   than an EPD-derived one.

The result is an :class:`AnimalSet` of EBV-scale predictions, which the
existing index pipeline (adjustment, scoring, sensitivity) consumes
unchanged. Inputs are assumed already age-standardized (e.g. 205-day
weaning weight); the engine does not re-adjust for age.

Reference: standard mass-selection theory (Falconer & Mackay 1996,
Ch. 10; BIF Guidelines). NexGenIQ phenotype-input feature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean

from .animal import Animal, AnimalSet, EpdScale, EpdValue
from .parameters import GeneticParameterSet


class PhenotypeInputError(Exception):
    """Raised when phenotype input is missing or unusable.

    The message is plain-language so a producer entering their own
    records sees exactly what is wrong and how to fix it.
    """


@dataclass
class PhenotypeRecord:
    """One animal's raw, age-standardized performance records.

    Attributes
    ----------
    animal_id:
        Stable identifier (tag, registration number, etc.).
    contemporary_group:
        Label of the group this animal was managed and measured with
        (e.g. ``"2025-spring-bulls"``). Animals are only ever compared
        within a contemporary group.
    breed:
        Breed code, used downstream for across-breed adjustment.
    phenotypes:
        Mapping of trait code -> measured, age-standardized value.
    sex:
        Optional sex code, carried for reporting.
    """

    animal_id: str
    contemporary_group: str
    breed: str = "Angus"
    phenotypes: dict[str, float] = field(default_factory=dict)
    sex: str = ""


@dataclass
class ContemporaryGroupSummary:
    """Per-trait summary of one contemporary group, for the audit trail."""

    contemporary_group: str
    trait_code: str
    n: int
    mean: float


@dataclass
class PhenotypeConversion:
    """Result of converting a set of phenotype records to breeding values.

    Attributes
    ----------
    animal_set:
        The candidate animals, carrying EBV-scale predictions ready for
        the index engine.
    group_summaries:
        Per-(group, trait) means and counts used in the adjustment, kept
        so the reproducibility ledger can show exactly how each phenotype
        was adjusted.
    warnings:
        Plain-language warnings (e.g. contemporary groups too small to
        adjust meaningfully).
    """

    animal_set: AnimalSet
    group_summaries: list[ContemporaryGroupSummary] = field(
        default_factory=list
    )
    warnings: list[str] = field(default_factory=list)


# A contemporary group with fewer than this many animals cannot give a
# trustworthy group mean; the deviation for such an animal is essentially
# uninformative. The conversion still runs (so a small herd is not locked
# out) but the result carries a warning.
_MIN_GROUP_SIZE = 3


def own_performance_accuracy(heritability: float) -> float:
    """Return the BIF accuracy of a single own-performance record.

    For one phenotypic record on the animal itself, the accuracy of the
    breeding-value prediction is ``sqrt(h2)`` (the correlation between
    the own-phenotype predictor and the true breeding value).

    Parameters
    ----------
    heritability:
        Trait heritability, in ``(0, 1]``.
    """
    if not 0.0 < heritability <= 1.0:
        raise PhenotypeInputError(
            f"Heritability must be between 0 and 1; got {heritability}."
        )
    return heritability ** 0.5


def convert_phenotypes(
    records: list[PhenotypeRecord],
    params: GeneticParameterSet,
    traits: list[str],
    evaluation_label: str = "own-performance (phenotype)",
) -> PhenotypeConversion:
    """Convert age-standardized phenotypes to an :class:`AnimalSet` of EBVs.

    For each trait, animals are grouped by contemporary group, the group
    mean is computed, and every animal's estimated breeding value is
    ``h2 * (phenotype - group_mean)`` on the EBV scale with accuracy
    ``sqrt(h2)``.

    Parameters
    ----------
    records:
        The producer's phenotype records. Each must carry a
        contemporary-group label.
    params:
        The genetic-parameter set supplying each trait's heritability.
    traits:
        Trait codes to convert. A trait with no phenotype column on any
        animal is skipped with a warning rather than failing the run.
    evaluation_label:
        Identifier written to every animal's ``evaluation_id`` so the
        reproducibility ledger records that this run used
        phenotype-derived breeding values.

    Returns
    -------
    PhenotypeConversion
        The animal set plus the contemporary-group audit trail and any
        warnings.

    Raises
    ------
    PhenotypeInputError
        If no records are supplied, a record has no contemporary group,
        or none of the requested traits has any phenotype data.
    """
    if not records:
        raise PhenotypeInputError(
            "No phenotype records were supplied. Provide at least one "
            "animal with measured performance data."
        )
    for rec in records:
        if not rec.contemporary_group:
            raise PhenotypeInputError(
                f"Animal {rec.animal_id!r} has no contemporary group. "
                f"Every animal must state which group it was managed and "
                f"measured with, so its performance can be compared "
                f"fairly within that group."
            )

    warnings: list[str] = []
    summaries: list[ContemporaryGroupSummary] = []

    # Build, per trait, the per-contemporary-group mean of the animals
    # that actually have a record for that trait.
    group_means: dict[tuple[str, str], float] = {}
    usable_traits: list[str] = []
    for trait in traits:
        if trait not in params.trait_params:
            warnings.append(
                f"Trait {trait!r} is not in the genetic-parameter set "
                f"and was skipped."
            )
            continue
        # Collect values per contemporary group.
        per_group: dict[str, list[float]] = {}
        for rec in records:
            if trait in rec.phenotypes:
                per_group.setdefault(rec.contemporary_group, []).append(
                    rec.phenotypes[trait]
                )
        if not per_group:
            warnings.append(
                f"No animal has a phenotype for trait {trait!r}; it was "
                f"skipped. Add a column for it, or remove it from the "
                f"breeding goal."
            )
            continue
        usable_traits.append(trait)
        for group, values in per_group.items():
            mean = fmean(values)
            group_means[(trait, group)] = mean
            summaries.append(
                ContemporaryGroupSummary(
                    contemporary_group=group,
                    trait_code=trait,
                    n=len(values),
                    mean=mean,
                )
            )
            if len(values) < _MIN_GROUP_SIZE:
                warnings.append(
                    f"Contemporary group {group!r} has only {len(values)} "
                    f"animal(s) with a {trait} record. A group this small "
                    f"gives an unreliable group average, so the adjusted "
                    f"value for these animals is weak — treat their "
                    f"{trait} ranking with caution."
                )

    if not usable_traits:
        raise PhenotypeInputError(
            "None of the breeding-goal traits has any phenotype data. "
            "Check that the uploaded columns match the goal's traits."
        )

    # Convert each animal's phenotypes to EBV-scale predictions.
    animals: list[Animal] = []
    for rec in records:
        epds: dict[str, EpdValue] = {}
        for trait in usable_traits:
            if trait not in rec.phenotypes:
                continue  # missing trait for this animal; validation notes it
            h2 = params.trait_params[trait].heritability
            mean = group_means[(trait, rec.contemporary_group)]
            deviation = rec.phenotypes[trait] - mean
            ebv = h2 * deviation
            epds[trait] = EpdValue(
                trait_code=trait,
                value=ebv,
                bif_accuracy=own_performance_accuracy(h2),
                scale=EpdScale.EBV,
            )
        animals.append(
            Animal(
                animal_id=rec.animal_id,
                breed=rec.breed,
                epds=epds,
                evaluation_id=evaluation_label,
                sex=rec.sex,
            )
        )

    return PhenotypeConversion(
        animal_set=AnimalSet(animals=animals, name="phenotype-derived"),
        group_summaries=summaries,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Producer-facing column names
# ---------------------------------------------------------------------------
# The phenotype CSV uses the names producers actually use for their
# measurements. Three of them map to a differently-coded engine trait:
#   IMF  (intramuscular fat %)  -> MARB  (the marbling trait)
#   BF   (backfat thickness)    -> FAT
#   LPAP (latent PAP)           -> PAP_L
# All other names match the engine trait code directly.
PHENOTYPE_COLUMN_TO_TRAIT: dict[str, str] = {
    "WW": "WW",
    "YW": "YW",
    "BW": "BW",
    "IMF": "MARB",
    "REA": "REA",
    "BF": "FAT",
    "DMI": "DMI",
    "RFI": "RFI",
    "DOC": "DOC",
    "PAP": "PAP",
    "LPAP": "PAP_L",
}

# The fixed (non-trait) columns every phenotype file carries.
_PHENOTYPE_META_COLUMNS = {
    "animal id": "animal_id",
    "breed": "breed",
    "sex": "sex",
    "contemporary group": "contemporary_group",
}


def parse_phenotype_rows(rows: list[dict]) -> list[PhenotypeRecord]:
    """Turn parsed CSV rows into :class:`PhenotypeRecord` objects.

    Each row is a mapping of column header -> string value, as produced by
    ``csv.DictReader``. Column matching is case-insensitive. The fixed
    columns are Animal ID, Breed, Sex and Contemporary Group; every other
    recognised column is a measured phenotype (see
    :data:`PHENOTYPE_COLUMN_TO_TRAIT`). Blank phenotype cells are skipped
    so a producer need not measure every trait on every animal.

    Parameters
    ----------
    rows:
        Parsed CSV rows.

    Returns
    -------
    list[PhenotypeRecord]

    Raises
    ------
    PhenotypeInputError
        If a row has no animal id, or a phenotype cell is non-numeric.
    """
    # Build a case-insensitive column -> trait lookup once.
    trait_lookup = {k.lower(): v for k, v in PHENOTYPE_COLUMN_TO_TRAIT.items()}
    records: list[PhenotypeRecord] = []
    for i, row in enumerate(rows, start=1):
        norm = {(k or "").strip().lower(): (v or "").strip()
                for k, v in row.items()}
        animal_id = norm.get("animal id", "")
        if not animal_id:
            raise PhenotypeInputError(
                f"Row {i} has no Animal ID. Every animal needs an "
                f"identifier."
            )
        phenotypes: dict[str, float] = {}
        for col, raw in norm.items():
            trait = trait_lookup.get(col)
            if trait is None or raw == "":
                continue
            try:
                phenotypes[trait] = float(raw)
            except ValueError:
                raise PhenotypeInputError(
                    f"Row {i} ({animal_id}): the {col.upper()} value "
                    f"{raw!r} is not a number."
                ) from None
        records.append(
            PhenotypeRecord(
                animal_id=animal_id,
                contemporary_group=norm.get("contemporary group", ""),
                breed=norm.get("breed", "Angus") or "Angus",
                phenotypes=phenotypes,
                sex=norm.get("sex", ""),
            )
        )
    return records
