"""
Database setup for the NexGenIQ backend.

Provides the SQLAlchemy engine, session factory, declarative base, and the
FastAPI dependency that yields a request-scoped session.

The default database is SQLite for zero-config local development; a
deployment points the database URL at PostgreSQL (Phase 3 Part 3C
Section 3.1). Nothing in the model layer is SQLite-specific.

The engine is created LAZILY - on first use, not at import time. This
matters for deployment robustness: if the database URL is misconfigured
or its driver is missing, importing this module must still succeed, so
the app can come up and report the problem via /health rather than
crashing the whole process before anything can handle it.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

# Lazily-initialised engine and session factory. None until first use.
_engine: Engine | None = None
_session_factory: sessionmaker | None = None


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def get_engine() -> Engine:
    """Return the SQLAlchemy engine, creating it on first call.

    Creating the engine here (rather than at module import) means an
    import never fails because of a database problem; the failure, if
    any, happens at first use and can be caught and reported.
    """
    global _engine
    if _engine is None:
        url = _settings.database_url
        # SQLite needs check_same_thread disabled to be used across
        # FastAPI's threadpool; the flag is ignored for other backends.
        connect_args = (
            {"check_same_thread": False}
            if url.startswith("sqlite")
            else {}
        )
        _engine = create_engine(
            url, connect_args=connect_args, echo=False, future=True
        )
    return _engine


def _get_session_factory() -> sessionmaker:
    """Return the session factory, creating it on first call."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            future=True,
        )
    return _session_factory


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped database session.

    The session is always closed when the request finishes, even on
    error.
    """
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Idempotent - safe to call on every startup.

    A production deployment would use Alembic migrations instead; for the
    MVP, create-all keeps local setup to zero steps. Any database problem
    raises here, where the caller (the app lifespan handler) catches it.
    """
    # Import models so they are registered on the metadata before
    # create_all runs.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
