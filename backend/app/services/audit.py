"""
Audit-logging helper for the NexGenIQ backend.

Records significant user actions to the :class:`AuditEvent` table so the
admin activity log can show what happened, who did it and when, with a
short non-sensitive summary.

Design rules:

* **Logging never breaks the action.** :func:`record_event` swallows any
  error -- if the log write fails, the user's request still succeeds.
  An audit log is useful, but it must not be able to take the app down.
* **Summaries are non-sensitive.** Callers pass a short plain-language
  description ("imported 42 animals", "built index with 5 traits"). The
  summary must never contain passwords, security answers, full payloads
  or a user's herd data -- only a one-line description.
* **Append-only.** Rows are inserted, never updated or deleted here.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import AuditEvent, User

logger = logging.getLogger("nexgeniq.audit")

# The recognised event types. Keeping these to a known set keeps the
# activity-log filter tidy and prevents typos creating phantom categories.
EVENT_TYPES = {
    "register",
    "login",
    "login_failed",
    "password_reset",
    "index_build",
    "simulation_run",
    "file_import",
    "admin_action",
}


def record_event(
    db: Session,
    *,
    event_type: str,
    summary: str,
    user: User | None = None,
    user_email: str = "",
) -> None:
    """Record one audit event. Never raises.

    Parameters
    ----------
    db:
        The request-scoped database session.
    event_type:
        A short event code; should be one of :data:`EVENT_TYPES`.
    summary:
        A short, non-sensitive, plain-language description of the event.
        Truncated to fit the column if necessary.
    user:
        The acting user, if known.
    user_email:
        The acting email, used when ``user`` is not available (for
        example a failed login for an unknown address).

    Any failure -- a bad session, a missing table -- is logged and
    swallowed, so a logging problem can never break the caller's request.
    """
    try:
        email = user.email if user is not None else user_email
        event = AuditEvent(
            event_type=event_type,
            summary=summary[:300],
            user_id=user.id if user is not None else None,
            user_email=email or "",
        )
        db.add(event)
        db.commit()
    except Exception:  # noqa: BLE001 - logging must never break the action
        # Roll back so the failed audit insert does not poison the
        # session for whatever the caller does next.
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        logger.warning(
            "audit event %r could not be recorded", event_type,
            exc_info=True,
        )
