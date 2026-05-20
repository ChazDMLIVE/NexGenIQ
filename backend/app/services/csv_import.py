"""
CSV animal/EPD import for the NexGenIQ backend.

Sale catalogues and breed-association exports arrive as messy CSV files.
This service parses an uploaded CSV, auto-detects which column maps to which
NexGenIQ field, and produces a structured preview plus the imported animals
— the column-mapping workflow of NexGenIQ Phase 3.5 Section 4.3.

The MVP supports a guided two-step flow: (1) ``inspect_csv`` returns the
detected column mapping for the user to confirm or correct; (2)
``parse_animals`` applies a confirmed mapping to produce animal records.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from osit_index import TRAIT_REGISTRY

# Recognised non-trait fields the importer can map a column to.
_SPECIAL_FIELDS = {"animal_id", "breed", "sex", "evaluation_id"}

# Header keywords that hint at the special fields, for auto-detection.
_FIELD_HINTS = {
    "animal_id": ["id", "reg", "tag", "animal", "ref", "registration"],
    "breed": ["breed"],
    "sex": ["sex", "gender"],
    "evaluation_id": ["evaluation", "eval"],
}


@dataclass
class ColumnMapping:
    """A proposed mapping from one CSV column to a NexGenIQ field.

    Attributes
    ----------
    source_column:
        The header text as it appears in the uploaded file.
    target_field:
        The NexGenIQ field, e.g. ``"animal_id"``, a trait code like
        ``"WW"``, ``"WW_acc"`` for an accuracy column, or ``""`` if the
        column is unmapped.
    confidence:
        ``"detected"`` (auto-matched with confidence) or ``"unmatched"``
        (needs the user to confirm).
    """

    source_column: str
    target_field: str = ""
    confidence: str = "unmatched"


@dataclass
class CsvInspection:
    """The result of inspecting an uploaded CSV.

    Attributes
    ----------
    columns:
        Proposed :class:`ColumnMapping` for every column.
    preview_rows:
        The first few data rows, for the UI preview.
    row_count:
        Total data rows in the file.
    """

    columns: list[ColumnMapping] = field(default_factory=list)
    preview_rows: list[dict[str, str]] = field(default_factory=list)
    row_count: int = 0


def _normalise(header: str) -> str:
    """Lower-case a header and strip non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]", "", header.lower())


def _detect_field(header: str) -> tuple[str, str]:
    """Guess the NexGenIQ field for a CSV column header.

    Returns ``(target_field, confidence)``. Detection logic, in order:

    1. An exact trait code (``"WW"``) or trait code + accuracy suffix
       (``"WW acc"``, ``"WW_accuracy"``) -> that trait or its accuracy.
    2. A special-field keyword (``"reg #"`` -> ``animal_id``).
    3. Otherwise unmatched.
    """
    norm = _normalise(header)

    # Trait or trait-accuracy column.
    for code in TRAIT_REGISTRY:
        c = code.lower()
        if norm == c:
            return code, "detected"
        if norm in (f"{c}epd", f"{c}value"):
            return code, "detected"
        if norm in (f"{c}acc", f"{c}accuracy", f"{c}acccuracy"):
            return f"{code}_acc", "detected"

    # Special field.
    for special, hints in _FIELD_HINTS.items():
        if any(h in norm for h in hints):
            return special, "detected"

    return "", "unmatched"


def inspect_csv(content: bytes, preview_n: int = 5) -> CsvInspection:
    """Parse a CSV's header and propose a column mapping.

    Parameters
    ----------
    content:
        The raw uploaded file bytes.
    preview_n:
        How many data rows to include in the preview.

    Returns
    -------
    CsvInspection
        The proposed mapping and a small preview for the user to confirm.
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return CsvInspection()

    headers = [h.strip() for h in rows[0]]
    columns = []
    for h in headers:
        target, conf = _detect_field(h)
        columns.append(ColumnMapping(h, target, conf))

    data_rows = rows[1:]
    preview = [
        dict(zip(headers, r))
        for r in data_rows[:preview_n]
    ]
    return CsvInspection(
        columns=columns, preview_rows=preview, row_count=len(data_rows)
    )


def parse_animals(
    content: bytes,
    mapping: dict[str, str],
) -> tuple[list[dict], list[str]]:
    """Apply a confirmed column mapping to produce animal records.

    Parameters
    ----------
    content:
        The raw uploaded file bytes.
    mapping:
        Confirmed mapping of ``source_column -> target_field``. Columns
        mapped to ``""`` are ignored.

    Returns
    -------
    (animals, problems)
        ``animals`` is a list of dicts in the :class:`AnimalIn` JSON shape.
        ``problems`` is a list of plain-language warnings (e.g. a row with
        no animal id) — surfaced to the user, never silently dropped.
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    animals: list[dict] = []
    problems: list[str] = []

    for line_no, row in enumerate(reader, start=2):
        record: dict = {
            "animal_id": "",
            "breed": "",
            "sex": "",
            "evaluation_id": "",
            "epds": [],
        }
        # epd_values[trait] = {"value": x, "bif_accuracy": y}
        epd_values: dict[str, dict] = {}

        for source_col, raw in row.items():
            target = mapping.get(source_col, "")
            if not target or raw is None or raw.strip() == "":
                continue
            value = raw.strip()

            if target in _SPECIAL_FIELDS:
                record[target] = value
            elif target.endswith("_acc"):
                trait = target[:-4]
                acc = _to_float(value)
                if acc is not None:
                    epd_values.setdefault(trait, {})["bif_accuracy"] = acc
            else:  # a trait EPD value
                num = _to_float(value)
                if num is not None:
                    epd_values.setdefault(target, {})["value"] = num

        if not record["animal_id"]:
            problems.append(
                f"Row {line_no} was skipped because it has no animal id."
            )
            continue

        record["epds"] = [
            {
                "trait_code": trait,
                "value": vals["value"],
                "bif_accuracy": vals.get("bif_accuracy"),
                "scale": "EPD",
            }
            for trait, vals in epd_values.items()
            if "value" in vals
        ]
        animals.append(record)

    return animals, problems


def _to_float(value: str) -> float | None:
    """Parse a numeric cell, tolerating stray commas/percent signs.

    Returns ``None`` for non-numeric cells (so the caller can flag them).
    """
    cleaned = value.replace(",", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
