"""
Multi-format animal-file import for the NexGenIQ backend.

The animal-import flow (``csv_import``) works on raw CSV bytes: it inspects
the header, proposes a column mapping for the user to confirm, then parses
the rows. This module lets that same flow accept two further formats by
**converting them to CSV bytes up front**:

* **Spreadsheets** (``.xlsx``) — a clean breed-association or records
  export. The first worksheet's row 1 is the header; the rest are animals.
  This is reliable.

* **Tabular EPD-list PDFs** — a text-based PDF whose content is a
  fixed-column table of animals and their EPDs (for example a breeder's
  "updated EPDs" sheet). ``pdfplumber`` extracts the table; the result is
  reliable *for this kind of PDF* but the user must still confirm the
  parsed table on the column-mapping screen, because a PDF can always be
  misread.

What this module deliberately does **not** do is read a designed sale
catalogue — a marketing document with pedigree panels, photos and prose.
Those are not machine-readable as structured data, and pretending to read
them would silently feed wrong EPDs into a ranking. A PDF whose pages do
not contain a single consistent table is rejected with a plain-language
message telling the user to obtain the seller's data export instead.

After conversion, control returns to :mod:`csv_import`: same column
detection, same confirm-the-mapping step, same parser.
"""

from __future__ import annotations

import csv
import io


class FileImportError(Exception):
    """Raised when an uploaded file cannot be turned into a usable table.

    The message is plain-language so the user knows exactly what to do
    (for example, "ask the seller for a spreadsheet export").
    """


def _rows_to_csv_bytes(rows: list[list[str]]) -> bytes:
    """Serialise a list of string rows to UTF-8 CSV bytes."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Spreadsheet (.xlsx) import
# ---------------------------------------------------------------------------
def xlsx_to_csv_bytes(content: bytes) -> bytes:
    """Convert the first worksheet of an .xlsx file to CSV bytes.

    Row 1 is treated as the header. Empty trailing rows are dropped. Every
    cell is stringified so the downstream CSV parser sees uniform text.

    Raises
    ------
    FileImportError
        If the workbook cannot be opened or has no data rows.
    """
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise FileImportError(
            "Spreadsheet support is not available on this server."
        ) from exc

    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(content), data_only=True, read_only=True
        )
    except Exception as exc:
        raise FileImportError(
            "That file could not be read as an Excel spreadsheet. Check "
            "it is a valid .xlsx file, or save it as CSV and try again."
        ) from exc

    worksheet = workbook.active
    rows: list[list[str]] = []
    for raw in worksheet.iter_rows(values_only=True):
        # Skip fully empty rows (common trailing blanks in exports).
        if all(cell is None or str(cell).strip() == "" for cell in raw):
            continue
        rows.append(
            ["" if cell is None else str(cell).strip() for cell in raw]
        )

    if len(rows) < 2:
        raise FileImportError(
            "That spreadsheet has no animal rows. The first row should be "
            "column headers, with one animal per row below it."
        )
    return _rows_to_csv_bytes(rows)


# ---------------------------------------------------------------------------
# Tabular EPD-list PDF import
# ---------------------------------------------------------------------------
# A page is treated as a usable EPD table only if it yields a table with at
# least this many columns -- a real EPD list has an id column plus several
# trait columns.
_MIN_TABLE_COLUMNS = 5

# A real EPD-list header is mostly filled in. A catalogue's per-lot fragment
# has a header full of blank/None cells. Require at least this fraction of
# header cells to be non-empty.
_MIN_HEADER_FILL = 0.7

# A real EPD list also names an identifier column. At least one header cell
# must look like an id/lot/registration column, or the file is not a list.
_ID_HEADER_HINTS = (
    "id", "reg", "tag", "tattoo", "lot", "animal", "ear", "asa", "aaa",
)

# The catalogue-rejection message, shared by every "this is not a list" exit.
_NOT_A_LIST_MESSAGE = (
    "This PDF does not contain a readable table of animals and EPDs. "
    "Designed sale catalogues -- with pedigree panels, photos and "
    "descriptions -- cannot be read as data, because the figures are "
    "scattered across the page rather than in one consistent table. Ask "
    "the seller for a spreadsheet or EPD-list export (CSV or Excel), or "
    "enter the animals you are interested in by hand."
)


def _looks_like_epd_header(header: list[str]) -> bool:
    """Return True if a row looks like a real EPD-list header.

    A genuine EPD-list header is mostly filled in and names an identifier
    column. A sale catalogue's per-lot fragment fails both checks: its
    extracted "header" is largely blank and names no id column.
    """
    if len(header) < _MIN_TABLE_COLUMNS:
        return False
    filled = sum(1 for cell in header if cell.strip())
    if filled / len(header) < _MIN_HEADER_FILL:
        return False
    norm = [cell.strip().lower() for cell in header]
    return any(
        any(hint in cell for hint in _ID_HEADER_HINTS) for cell in norm
    )


def pdf_to_csv_bytes(content: bytes) -> bytes:
    """Convert a tabular EPD-list PDF to CSV bytes.

    Every page is searched for a ruled or aligned table. A page's table is
    accepted only if its first row :func:`_looks_like_epd_header` -- mostly
    filled, and naming an identifier column. The first such page sets the
    column structure; later pages contribute rows only when their table has
    the *same* header (a real multi-page EPD list repeats its header).

    A designed sale catalogue fails this: pdfplumber finds per-lot pedigree
    fragments whose "headers" are blank and inconsistent page to page. When
    no page yields a genuine EPD-list header, the file is rejected with a
    plain-language message -- never silently parsed into a wrong ranking.

    Raises
    ------
    FileImportError
        If no page contains a consistent EPD-list table.
    """
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise FileImportError(
            "PDF support is not available on this server."
        ) from exc

    try:
        pdf = pdfplumber.open(io.BytesIO(content))
    except Exception as exc:
        raise FileImportError(
            "That file could not be read as a PDF."
        ) from exc

    header: list[str] | None = None
    data_rows: list[list[str]] = []

    with pdf:
        for page in pdf.pages:
            try:
                table = page.extract_table()
            except Exception:
                table = None
            if not table or len(table) < 2:
                continue
            cleaned = [
                ["" if c is None else str(c).strip() for c in row]
                for row in table
            ]
            cleaned = [r for r in cleaned if any(cell for cell in r)]
            if not cleaned:
                continue

            if header is None:
                # Only adopt this page's first row as the header if it
                # genuinely looks like an EPD-list header.
                if _looks_like_epd_header(cleaned[0]):
                    header = cleaned[0]
                    data_rows.extend(cleaned[1:])
            elif (
                len(cleaned[0]) == len(header)
                and cleaned[0] == header
            ):
                # A true continuation page: the same header repeats.
                data_rows.extend(cleaned[1:])
            elif len(cleaned[0]) == len(header):
                # Same width but a different first row -- treat the whole
                # page as data rows of the established table.
                data_rows.extend(cleaned)

    if header is None or not data_rows:
        raise FileImportError(_NOT_A_LIST_MESSAGE)
    return _rows_to_csv_bytes([header, *data_rows])


# ---------------------------------------------------------------------------
# Format dispatch
# ---------------------------------------------------------------------------
def to_csv_bytes(filename: str, content: bytes) -> bytes:
    """Normalise any supported animal file to CSV bytes by extension.

    ``.csv`` content is returned unchanged; ``.xlsx``/``.xls`` and ``.pdf``
    are converted. An unsupported extension raises :class:`FileImportError`.

    The returned bytes are always plain CSV, so the existing
    :mod:`csv_import` inspect/confirm/parse flow handles every format
    identically from here on.
    """
    name = filename.lower().strip()
    if name.endswith(".csv"):
        return content
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        return xlsx_to_csv_bytes(content)
    if name.endswith(".pdf"):
        return pdf_to_csv_bytes(content)
    raise FileImportError(
        f"Unsupported file type: {filename}. Upload a CSV or Excel "
        f"spreadsheet, or a tabular EPD-list PDF."
    )
