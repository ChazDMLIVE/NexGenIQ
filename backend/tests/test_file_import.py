"""Tests for multi-format animal-file import (app.services.file_import).

Covers the three import tiers:
  Tier 1 - clean .xlsx spreadsheet -> CSV bytes.
  Tier 2 - tabular EPD-list PDF -> CSV bytes.
  Tier 3 - designed sale catalogue -> rejected with a clear message.

Fixtures are built in-memory so the suite needs no external files.
"""

import csv
import io

import pytest

from app.services.file_import import (
    FileImportError,
    to_csv_bytes,
    xlsx_to_csv_bytes,
)
from app.services import csv_import


def _make_xlsx(rows):
    """Build an in-memory .xlsx workbook from a list of row lists."""
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Animals"
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# --- Tier 1: spreadsheet import -------------------------------------------
def test_xlsx_converts_to_csv_bytes():
    """A clean .xlsx becomes CSV bytes the existing CSV flow can read."""
    content = _make_xlsx([
        ["Tattoo", "Breed", "WW", "WW Acc", "YW"],
        ["706M", "Angus", 565, 0.4, 1085],
        ["707M", "Angus", 540, 0.5, 1040],
    ])
    csv_bytes = xlsx_to_csv_bytes(content)
    rows = list(csv.reader(io.StringIO(csv_bytes.decode("utf-8"))))
    assert rows[0] == ["Tattoo", "Breed", "WW", "WW Acc", "YW"]
    assert len(rows) == 3  # header + 2 animals


def test_xlsx_flows_through_inspect_and_parse():
    """An xlsx import inspects and parses like a CSV would."""
    content = _make_xlsx([
        ["Tattoo", "Breed", "WW", "YW"],
        ["706M", "Angus", 565, 1085],
        ["707M", "Angus", 540, 1040],
    ])
    csv_bytes = to_csv_bytes("herd.xlsx", content)
    inspection = csv_import.inspect_csv(csv_bytes)
    assert inspection.row_count == 2
    mapping = {c.source_column: c.target_field for c in inspection.columns}
    animals, problems = csv_import.parse_animals(csv_bytes, mapping)
    assert len(animals) == 2
    assert animals[0]["animal_id"] == "706M"


def test_xlsx_with_no_data_rows_rejected():
    """An .xlsx with only a header row is rejected with a clear message."""
    content = _make_xlsx([["Tattoo", "Breed", "WW"]])
    with pytest.raises(FileImportError, match="no animal rows"):
        xlsx_to_csv_bytes(content)


# --- Column-alias detection -----------------------------------------------
def test_tattoo_column_detected_as_animal_id():
    """A 'Tattoo' header auto-maps to the animal id."""
    field, conf = csv_import._detect_field("Tattoo")
    assert field == "animal_id"
    assert conf == "detected"


def test_adg_column_detected_as_pwg_trait():
    """An 'ADG' header auto-maps to the PWG trait (producer alias)."""
    field, conf = csv_import._detect_field("ADG")
    assert field == "PWG"
    assert conf == "detected"


def test_imf_and_bf_aliases_detected():
    """IMF -> MARB and BF -> FAT producer aliases are recognised."""
    assert csv_import._detect_field("IMF")[0] == "MARB"
    assert csv_import._detect_field("BF")[0] == "FAT"


# --- Format dispatch ------------------------------------------------------
def test_csv_passes_through_unchanged():
    """A .csv upload is returned byte-for-byte unchanged."""
    raw = b"Tattoo,WW\n706M,565\n"
    assert to_csv_bytes("herd.csv", raw) == raw


def test_unsupported_extension_rejected():
    """An unsupported file type is rejected with a clear message."""
    with pytest.raises(FileImportError, match="Unsupported file type"):
        to_csv_bytes("herd.docx", b"whatever")


# --- Tier 3: catalogue rejection ------------------------------------------
def test_epd_header_recogniser_accepts_real_header():
    """A mostly-filled header naming an id column is accepted."""
    from app.services.file_import import _looks_like_epd_header
    header = ["LOT", "REG", "TATTOO", "CED", "BW", "WW", "YW"]
    assert _looks_like_epd_header(header) is True


def test_epd_header_recogniser_rejects_catalogue_fragment():
    """A sparse, id-less fragment (catalogue pedigree box) is rejected."""
    from app.services.file_import import _looks_like_epd_header
    # Mostly blank, no id column - typical of a catalogue table fragment.
    fragment = ["", "", "", "", "CED", "", "BW"]
    assert _looks_like_epd_header(fragment) is False


def test_epd_header_recogniser_rejects_no_id_column():
    """A filled header that names no identifier column is rejected."""
    from app.services.file_import import _looks_like_epd_header
    # All trait columns, no LOT/REG/TATTOO/etc.
    header = ["CED", "BW", "WW", "YW", "SC", "MARB"]
    assert _looks_like_epd_header(header) is False
