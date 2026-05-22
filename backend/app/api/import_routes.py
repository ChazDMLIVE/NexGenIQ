"""
Animal-file import API endpoints for NexGenIQ.

Implements the guided import flow of NexGenIQ Phase 3.5 Section 4.3:
inspect an uploaded file to propose a column mapping, then parse it with a
confirmed mapping into animal records.

Three upload formats are accepted. A CSV is used directly; an Excel
spreadsheet (.xlsx) and a tabular EPD-list PDF are first normalised to CSV
by :mod:`app.services.file_import` -- so from the inspect step onward every
format flows through the same column-detection, confirm, and parse path.
A designed sale-catalogue PDF (pedigree panels, photos, prose) is not
machine-readable and is rejected with a plain-language message.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.models import User
from app.services import csv_import
from app.services.file_import import FileImportError, to_csv_bytes

router = APIRouter(prefix="/import", tags=["import"])

# Largest upload the import endpoints will accept. An animal file -- a
# CSV, a spreadsheet, or a tabular EPD-list PDF -- is small in practice;
# this cap (15 MB) is generous for a real herd file but bounds memory so
# an oversized or maliciously-crafted file cannot exhaust the server when
# openpyxl/pdfplumber expands it.
_MAX_UPLOAD_BYTES = 15 * 1024 * 1024


async def _read_capped(file: UploadFile) -> bytes:
    """Read an upload, rejecting anything larger than the size cap.

    The file is read in 1 MB chunks so an oversized upload is refused as
    soon as it crosses the cap, without holding the whole file in memory.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > _MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"That file is too large. The import accepts files up "
                    f"to {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB; for a "
                    f"larger data set, split it into smaller files."
                ),
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/inspect")
async def inspect(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> dict:
    """Inspect an uploaded animal file and propose a column mapping.

    Accepts CSV, Excel (.xlsx) or a tabular EPD-list PDF. The file is
    normalised to CSV, then inspected. Returns the detected mapping for
    every column, a small preview, and the row count -- the data the
    column-mapping screen needs so the user can confirm or correct the
    auto-detection before anything is imported.
    """
    raw = await _read_capped(file)
    try:
        content = to_csv_bytes(file.filename or "", raw)
    except FileImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    inspection = csv_import.inspect_csv(content)
    return {
        "filename": file.filename,
        "row_count": inspection.row_count,
        "columns": [
            {
                "source_column": c.source_column,
                "target_field": c.target_field,
                "confidence": c.confidence,
            }
            for c in inspection.columns
        ],
        "preview_rows": inspection.preview_rows,
    }


@router.post("/parse")
async def parse(
    file: UploadFile = File(...),
    mapping_json: str = Form(...),
    user: User = Depends(get_current_user),
) -> dict:
    """Parse an uploaded animal file using a confirmed column mapping.

    Parameters
    ----------
    file:
        The same file that was inspected (CSV, .xlsx or tabular PDF).
    mapping_json:
        A JSON object mapping ``source_column`` -> ``target_field``, as
        confirmed by the user on the column-mapping screen.

    Returns
    -------
    dict
        ``animals`` -- parsed records in the API animal shape -- and
        ``problems`` -- plain-language warnings about skipped/odd rows.
    """
    raw = await _read_capped(file)
    try:
        content = to_csv_bytes(file.filename or "", raw)
    except FileImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        mapping = json.loads(mapping_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The column mapping was not valid JSON.",
        ) from exc
    if not isinstance(mapping, dict):
        raise HTTPException(
            status_code=400,
            detail="The column mapping must be a JSON object.",
        )

    animals, problems = csv_import.parse_animals(content, mapping)
    return {
        "animal_count": len(animals),
        "animals": animals,
        "problems": problems,
    }
