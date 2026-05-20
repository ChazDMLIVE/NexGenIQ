"""
CSV import API endpoints for NexGenIQ.

Implements the two-step guided import flow of NexGenIQ Phase 3.5 Section
4.3: inspect an uploaded file to propose a column mapping, then parse the
file with a confirmed mapping into animal records.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_current_user
from app.models import User
from app.services import csv_import

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/inspect")
async def inspect(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> dict:
    """Inspect an uploaded CSV and propose a column mapping.

    Returns the detected mapping for every column, a small preview, and the
    row count — the data the column-mapping screen needs so the user can
    confirm or correct the auto-detection.
    """
    content = await file.read()
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
    """Parse an uploaded CSV using a confirmed column mapping.

    Parameters
    ----------
    file:
        The same CSV that was inspected.
    mapping_json:
        A JSON object mapping ``source_column`` -> ``target_field``, as
        confirmed by the user on the column-mapping screen.

    Returns
    -------
    dict
        ``animals`` — parsed records in the API animal shape — and
        ``problems`` — plain-language warnings about skipped/odd rows.
    """
    import json

    content = await file.read()
    mapping = json.loads(mapping_json)
    animals, problems = csv_import.parse_animals(content, mapping)
    return {
        "animal_count": len(animals),
        "animals": animals,
        "problems": problems,
    }
