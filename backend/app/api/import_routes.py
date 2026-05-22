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
    raw = await file.read()
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
    raw = await file.read()
    try:
        content = to_csv_bytes(file.filename or "", raw)
    except FileImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mapping = json.loads(mapping_json)
    animals, problems = csv_import.parse_animals(content, mapping)
    return {
        "animal_count": len(animals),
        "animals": animals,
        "problems": problems,
    }
