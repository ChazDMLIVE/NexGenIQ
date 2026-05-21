"""
Saved-work API endpoints for NexGenIQ.

A user can explicitly save a completed index ranking, a completed
herd-simulation result, or a breeding goal, and re-open or delete it
later. One table (``SavedItem``) backs all three kinds; nothing is saved
automatically.

A generous per-user cap bounds storage: saving is cheap (a saved item is
a small JSON blob, and re-opening it is a database read, not an engine
re-run), but the cap keeps total storage predictable and protects against
runaway use.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import SavedItem, User
from app.schemas import SavedItemCreate, SavedItemOut, SavedItemSummary

router = APIRouter(prefix="/saved", tags=["saved"])

# The most items one user may keep. Generous - almost no real user will
# reach it - but it bounds storage and gives a clear stopping point.
_MAX_SAVED_PER_USER = 50

# The kinds a saved item may be.
_VALID_KINDS = {"index_result", "simulation_result", "breeding_goal"}


@router.get("", response_model=list[SavedItemSummary])
def list_saved(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SavedItemSummary]:
    """List the current user's saved items, newest first.

    Payloads are omitted from the list for speed; fetch a single item to
    get its full payload.
    """
    rows = (
        db.execute(
            select(SavedItem)
            .where(SavedItem.owner_id == user.id)
            .order_by(SavedItem.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        SavedItemSummary(
            id=r.id,
            kind=r.kind,
            name=r.name,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("", response_model=SavedItemOut, status_code=201)
def create_saved(
    request: SavedItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SavedItemOut:
    """Save a piece of work for the current user.

    Rejects an unknown kind, and enforces the per-user cap with a clear
    message so the user knows to delete something before saving more.
    """
    if request.kind not in _VALID_KINDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unknown saved-item kind {request.kind!r}. Expected one "
                f"of: {', '.join(sorted(_VALID_KINDS))}."
            ),
        )

    current_count = (
        db.execute(
            select(SavedItem).where(SavedItem.owner_id == user.id)
        )
        .scalars()
        .all()
    )
    if len(current_count) >= _MAX_SAVED_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"You have reached the limit of {_MAX_SAVED_PER_USER} "
                f"saved items. Delete one from My Saved Work before "
                f"saving another."
            ),
        )

    item = SavedItem(
        owner_id=user.id,
        kind=request.kind,
        name=request.name,
        payload=request.payload,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return SavedItemOut(
        id=item.id,
        kind=item.kind,
        name=item.name,
        created_at=item.created_at.isoformat(),
        payload=item.payload,
    )


def _owned_item(item_id: str, db: Session, user: User) -> SavedItem:
    """Fetch one saved item, ensuring it belongs to the current user.

    A user can only ever see or touch their own saved items; a request
    for someone else's id returns 404 (not 403), so the existence of
    another user's item is not revealed.
    """
    item = db.get(SavedItem, item_id)
    if item is None or item.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That saved item was not found.",
        )
    return item


@router.get("/{item_id}", response_model=SavedItemOut)
def get_saved(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SavedItemOut:
    """Fetch one saved item in full, for re-opening it in its tool."""
    item = _owned_item(item_id, db, user)
    return SavedItemOut(
        id=item.id,
        kind=item.kind,
        name=item.name,
        created_at=item.created_at.isoformat(),
        payload=item.payload,
    )


@router.delete("/{item_id}", status_code=204)
def delete_saved(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete one of the current user's saved items."""
    item = _owned_item(item_id, db, user)
    db.delete(item)
    db.commit()
