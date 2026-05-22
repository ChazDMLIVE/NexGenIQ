"""
SQLAlchemy ORM models for the NexGenIQ backend.

These implement the data model of NexGenIQ Phase 3 Part 3C Section 3.3,
scoped to what Milestone 1 (the Index Builder) needs. The simulation-engine
entities (ProductionSystem, EconomicScenario, SimulationRun, DerivedMEV) are
specified in Phase 3 and will be added in Milestone 2 — the schema below is
deliberately compatible so that addition needs no rework.

All models use UUID string primary keys and carry created/updated
timestamps. JSONB-style flexible blobs are stored as JSON columns so the
same code runs on SQLite (development) and PostgreSQL (deployment).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    """Generate a new string UUID primary key."""
    return str(uuid.uuid4())


def _now() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adds created_at / updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


# ---------------------------------------------------------------------------
# Users and organisations
# ---------------------------------------------------------------------------
class Organisation(Base, TimestampMixin):
    """An organisation — a university, breed association or farm.

    Scopes datasets and members (Phase 3 Part 3C Section 3.3).
    """

    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_type: Mapped[str] = mapped_column(String(50), default="farm")

    users: Mapped[list["User"]] = relationship(back_populates="organisation")


class User(Base, TimestampMixin):
    """A user account.

    Roles (Phase 3 Part 3C Section 3.6): ``producer``, ``researcher``,
    ``breeder``, ``assoc_admin``, ``site_admin``. The role sets the UI
    default (guided vs full) and unlocks API scopes — it is a default, not
    a capability ceiling.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True,
                                       nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(30), default="producer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Security question for self-service password reset. The question text
    # is stored in the clear; the answer is bcrypt-hashed exactly like a
    # password and never stored in plain text. Both are nullable so
    # accounts created before this feature still load -- a user with no
    # question set is told to contact an administrator to reset.
    security_question: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    security_answer_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    organisation_id: Mapped[str | None] = mapped_column(
        ForeignKey("organisations.id"), nullable=True
    )
    organisation: Mapped["Organisation | None"] = relationship(
        back_populates="users"
    )


# ---------------------------------------------------------------------------
# Genetic parameter sets
# ---------------------------------------------------------------------------
class GeneticParameterSet(Base, TimestampMixin):
    """A stored genetic-parameter set.

    ``scope`` is ``consensus`` (the built-in library), ``breed`` (a
    breed-specific override) or ``user`` (uploaded by a researcher). The
    ``data`` blob holds per-trait parameters and the genetic correlations
    in the JSON shape the engine consumes.
    """

    __tablename__ = "genetic_parameter_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="v1")
    scope: Mapped[str] = mapped_column(String(20), default="user")
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


# ---------------------------------------------------------------------------
# Across-breed adjustment factor tables
# ---------------------------------------------------------------------------
class AdjustmentFactorTable(Base, TimestampMixin):
    """A versioned USMARC/BIF across-breed adjustment-factor table.

    The ``factors`` blob maps ``"breed|trait"`` keys to factor values.
    """

    __tablename__ = "adjustment_factor_tables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    base_breed: Mapped[str] = mapped_column(String(50), default="Angus")
    factors: Mapped[dict] = mapped_column(JSON, default=dict)


# ---------------------------------------------------------------------------
# Datasets and animals
# ---------------------------------------------------------------------------
class Dataset(Base, TimestampMixin):
    """A collection of candidate animals (e.g. a sale catalogue).

    ``path`` supports the wildcard access-control model of Phase 3
    Part 3C Section 3.6.
    """

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str] = mapped_column(String(255), default="")
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    animals: Mapped[list["AnimalRecord"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class AnimalRecord(Base, TimestampMixin):
    """A candidate animal and its EPDs.

    The ``epds`` blob maps trait code to ``{value, accuracy, scale}`` —
    the JSON shape the engine's :class:`Animal` is built from.
    """

    __tablename__ = "animal_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    animal_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    breed: Mapped[str] = mapped_column(String(60), default="")
    sex: Mapped[str] = mapped_column(String(10), default="")
    evaluation_id: Mapped[str] = mapped_column(String(120), default="")
    epds: Mapped[dict] = mapped_column(JSON, default=dict)

    dataset: Mapped["Dataset"] = relationship(back_populates="animals")


# ---------------------------------------------------------------------------
# Breeding goals and index scenarios
# ---------------------------------------------------------------------------
class BreedingGoal(Base, TimestampMixin):
    """A stored breeding goal — goal traits, economic weights, basis.

    ``components`` is a list of ``{trait_code, economic_weight}``.
    ``source`` is ``manual``, ``preset`` or ``simulation``.
    """

    __tablename__ = "breeding_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    basis: Mapped[str] = mapped_column(String(30),
                                       default="per_cow_exposed")
    components: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class IndexScenario(Base, TimestampMixin):
    """A reusable index definition: goal + parameters + mode + settings."""

    __tablename__ = "index_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    breeding_goal_id: Mapped[str] = mapped_column(
        ForeignKey("breeding_goals.id")
    )
    parameter_set_id: Mapped[str | None] = mapped_column(
        ForeignKey("genetic_parameter_sets.id"), nullable=True
    )
    dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("datasets.id"), nullable=True
    )
    adjustment_table_id: Mapped[str | None] = mapped_column(
        ForeignKey("adjustment_factor_tables.id"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(30), default="economic_weight")
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


# ---------------------------------------------------------------------------
# Reproducibility ledger
# ---------------------------------------------------------------------------
class RunLedger(Base, TimestampMixin):
    """The reproducibility ledger — one row per engine execution.

    Records exactly what produced a result so any run can be reproduced and
    audited (Phase 2 gap G10; Phase 3 Part 3C Section 3.3).
    """

    __tablename__ = "run_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    scenario_id: Mapped[str | None] = mapped_column(String(36),
                                                    nullable=True)
    engine_version: Mapped[str] = mapped_column(String(80), default="")
    param_set_version: Mapped[str] = mapped_column(String(80), default="")
    adjustment_table_version: Mapped[str] = mapped_column(
        String(120), default=""
    )
    mode: Mapped[str] = mapped_column(String(30), default="")
    inputs_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    result_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class SavedItem(Base, TimestampMixin):
    """A piece of work a user has explicitly chosen to save.

    One table covers all three saved kinds - a completed index ranking,
    a completed herd-simulation result, and a standalone breeding goal -
    distinguished by ``kind``. The full inputs and result are kept in the
    ``payload`` JSON blob so a saved item can be re-opened in its tool
    without re-running any engine. Nothing is saved automatically; a row
    here exists only because the user pressed Save.
    """

    __tablename__ = "saved_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=_uuid)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    # One of: "index_result", "simulation_result", "breeding_goal".
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    # The user-given name for this saved item.
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # The complete inputs + result, in the JSON shape the relevant tool
    # consumes when the item is re-opened.
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
