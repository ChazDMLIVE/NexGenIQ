"""
Admin-panel API endpoints for NexGenIQ.

Every endpoint here is gated behind ``require_role("site_admin")`` -- a
non-admin token gets a 403. The admin panel lets the site administrator
see registered users, view what users have submitted, read the activity
log, and manage accounts (enable/disable, change role, reset a password).

Two safety rules protect the administrator from locking themselves out:
an admin cannot disable their own account, and an admin cannot remove
their own site_admin role.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.security import hash_password
from app.models import AuditEvent, SavedItem, User
from app.schemas import (
    AdminPasswordReset,
    AdminSavedItemOut,
    AdminUserOut,
    AdminUserUpdate,
    AuditEventOut,
)
from app.services.audit import record_event

router = APIRouter(prefix="/admin", tags=["admin"])

# The roles an admin may assign. site_admin is included so an admin can
# promote another account; the two self-protection rules below stop an
# admin demoting or disabling their own account.
_ASSIGNABLE_ROLES = {
    "producer", "researcher", "breeder", "assoc_admin", "site_admin",
}


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("site_admin")),
) -> list[AdminUserOut]:
    """List every registered user, newest first.

    For each account the response includes the role, whether it is
    active, whether it has a security question on file, and how many
    items the user has saved.
    """
    users = (
        db.execute(select(User).order_by(User.created_at.desc()))
        .scalars()
        .all()
    )
    out: list[AdminUserOut] = []
    for u in users:
        saved_count = (
            db.execute(
                select(SavedItem).where(SavedItem.owner_id == u.id)
            )
            .scalars()
            .all()
        )
        out.append(
            AdminUserOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                has_security_question=bool(
                    u.security_question and u.security_answer_hash
                ),
                created_at=u.created_at.isoformat(),
                saved_item_count=len(saved_count),
            )
        )
    return out


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("site_admin")),
) -> AdminUserOut:
    """Change a user's role or active status.

    Self-protection: an admin cannot disable their own account, and
    cannot change their own role away from site_admin -- either would
    risk locking the administrator out of the panel.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That user was not found.",
        )

    if payload.role is not None:
        if payload.role not in _ASSIGNABLE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown role {payload.role!r}.",
            )
        if user.id == admin.id and payload.role != "site_admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You cannot change your own role away from "
                    "site_admin."
                ),
            )
        user.role = payload.role

    if payload.is_active is not None:
        if user.id == admin.id and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot disable your own account.",
            )
        user.is_active = payload.is_active

    db.add(user)
    db.commit()
    db.refresh(user)

    record_event(
        db, event_type="admin_action",
        summary=(
            f"Admin updated account {user.email} "
            f"(role={user.role}, active={user.is_active})."
        ),
        user=admin,
    )

    saved_count = (
        db.execute(select(SavedItem).where(SavedItem.owner_id == user.id))
        .scalars()
        .all()
    )
    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        has_security_question=bool(
            user.security_question and user.security_answer_hash
        ),
        created_at=user.created_at.isoformat(),
        saved_item_count=len(saved_count),
    )


@router.post("/users/{user_id}/password", status_code=204)
def reset_user_password(
    user_id: str,
    payload: AdminPasswordReset,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("site_admin")),
) -> None:
    """Set a new password for a user account (admin-assisted reset).

    For when a user cannot self-reset -- for example an account with no
    security question on file.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That user was not found.",
        )
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()

    record_event(
        db, event_type="admin_action",
        summary=f"Admin reset the password for {user.email}.",
        user=admin,
    )


@router.get(
    "/users/{user_id}/saved-items",
    response_model=list[AdminSavedItemOut],
)
def user_saved_items(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("site_admin")),
) -> list[AdminSavedItemOut]:
    """List the saved work of one user, newest first.

    This is the submitted-data view: the index runs, simulations and
    breeding goals a user has chosen to save. Payloads are omitted from
    the list; an admin can already open a user's full data through the
    standard saved-item endpoint if needed.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That user was not found.",
        )
    rows = (
        db.execute(
            select(SavedItem)
            .where(SavedItem.owner_id == user_id)
            .order_by(SavedItem.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        AdminSavedItemOut(
            id=r.id,
            kind=r.kind,
            name=r.name,
            created_at=r.created_at.isoformat(),
            owner_email=user.email,
        )
        for r in rows
    ]


@router.get("/activity", response_model=list[AuditEventOut])
def activity_log(
    limit: int = 200,
    event_type: str = "",
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("site_admin")),
) -> list[AuditEventOut]:
    """Return the activity log, newest first.

    Parameters
    ----------
    limit:
        How many events to return (capped at 500).
    event_type:
        Optional filter -- return only events of this type.
    """
    capped = max(1, min(limit, 500))
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    rows = db.execute(query.limit(capped)).scalars().all()
    return [
        AuditEventOut(
            id=r.id,
            created_at=r.created_at.isoformat(),
            event_type=r.event_type,
            user_email=r.user_email,
            summary=r.summary,
        )
        for r in rows
    ]
