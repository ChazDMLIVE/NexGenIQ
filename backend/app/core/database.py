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

from sqlalchemy import create_engine, inspect, text
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


# Columns added to existing tables after their first release. SQLAlchemy's
# create_all() only creates MISSING TABLES -- it never alters a table that
# already exists -- so a database created before one of these columns was
# added needs the column added explicitly. Each entry is
# (table, column, column DDL type). The DDL type uses portable SQL that
# works on both SQLite (development) and PostgreSQL (deployment).
_ADDED_COLUMNS: list[tuple[str, str, str]] = [
    ("users", "security_question", "VARCHAR(255)"),
    ("users", "security_answer_hash", "VARCHAR(255)"),
]


def _add_missing_columns(engine: Engine) -> None:
    """Add any post-release columns that an existing database is missing.

    This is a lightweight stand-in for a full migration tool: it inspects
    each table and issues an ``ALTER TABLE ... ADD COLUMN`` only for
    columns that are not already present. It is idempotent -- on a
    database that already has every column it does nothing -- so it is
    safe to run on every startup. New columns are added nullable, so
    existing rows are unaffected.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl_type in _ADDED_COLUMNS:
            if table not in existing_tables:
                # The table does not exist yet; create_all() will have
                # made it with the column already, so nothing to do.
                continue
            columns = {c["name"] for c in inspector.get_columns(table)}
            if column in columns:
                continue
            conn.execute(
                text(
                    f"ALTER TABLE {table} "
                    f"ADD COLUMN {column} {ddl_type}"
                )
            )


def init_db() -> None:
    """Create all tables and add any missing columns. Idempotent.

    ``create_all`` creates tables that do not exist; it does NOT alter a
    table that already exists. So after it runs, :func:`_add_missing_columns`
    brings an older database up to date by adding any columns introduced
    after that database was first created. Both steps are safe to run on
    every startup. A production deployment would use Alembic migrations
    instead; for the MVP this keeps setup to zero steps while still
    letting the schema evolve. Any database problem raises here, where the
    caller (the app lifespan handler) catches it.
    """
    # Import models so they are registered on the metadata before
    # create_all runs.
    from app import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _add_missing_columns(engine)


def bootstrap_admin() -> None:
    """Promote the designated admin account to the site_admin role.

    The admin email comes from the NEXGENIQ_ADMIN_EMAIL environment
    variable. If that account exists and is not already a site_admin, its
    role is set to site_admin. This gives the deployment exactly one
    administrator with no manual database step, and is idempotent -- on
    every later startup it finds the account already an admin and does
    nothing. If the variable is blank, or names an account that does not
    exist yet, this is a no-op (the account can be promoted on a later
    startup once it has registered).
    """
    from app.models import User  # local import: models import this module

    email = _settings.admin_email.strip().lower()
    if not email:
        return
    factory = _get_session_factory()
    db = factory()
    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .one_or_none()
        )
        if user is not None and user.role != "site_admin":
            user.role = "site_admin"
            db.add(user)
            db.commit()
    finally:
        db.close()
