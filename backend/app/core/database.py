"""
Database setup for the NexGenIQ backend.

Provides the SQLAlchemy engine, session factory, declarative base, and the
FastAPI dependency that yields a request-scoped session.

The default database is SQLite for zero-config local development; a
deployment points :data:`Settings.database_url` at PostgreSQL (Phase 3
Part 3C Section 3.1). Nothing in the model layer is SQLite-specific.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

# SQLite needs check_same_thread disabled to be used across FastAPI's
# threadpool; the flag is harmless and ignored for other backends.
_connect_args = (
    {"check_same_thread": False}
    if _settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, future=True
)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped database session.

    The session is always closed when the request finishes, even on error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Idempotent — safe to call on every startup.

    A production deployment would use Alembic migrations instead; for the
    MVP, create-all keeps local setup to zero steps.
    """
    # Import models so they are registered on the metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
