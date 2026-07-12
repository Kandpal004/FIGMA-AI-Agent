"""ORM models — the persisted shape of the platform.

These mirror the Pydantic contracts in :mod:`core.contracts.workflow`: a
:class:`RunModel` is the durable form of a ``RunRecord`` and a
:class:`TransitionModel` the durable form of a ``TransitionRecord``. Keeping the
two representations aligned (ORM for storage, Pydantic for logic/transport) lets
the pure state machine stay database-free while everything is still persisted.

Multi-tenancy is baked in from row zero: every tenant-owned row carries a
``tenant_id`` foreign key. Retrofitting tenancy onto a live SaaS is one of the
most expensive migrations there is; we pay the trivial cost now (ADR-0007).

Schema migrations are managed by Alembic in a later phase; for local bring-up,
:func:`api.db.session.init_models` can create these tables directly.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from core.contracts.workflow import RunStatus, TransitionEvent, WorkflowState
from sqlalchemy import (
    JSON,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class TimestampMixin:
    """`created_at` / `updated_at` maintained by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantModel(Base, TimestampMixin):
    """A customer of the SaaS. The root of every ownership chain."""

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    runs: Mapped[list[RunModel]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class RunModel(Base, TimestampMixin):
    """A design run for a single page section — the durable form of a RunRecord."""

    __tablename__ = "runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    section: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[WorkflowState] = mapped_column(
        SAEnum(WorkflowState, name="workflow_state", native_enum=False, length=48),
        default=WorkflowState.CREATED,
        nullable=False,
        index=True,
    )
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status", native_enum=False, length=24),
        default=RunStatus.PENDING,
        nullable=False,
        index=True,
    )

    brief: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    artifacts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    redesign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    tenant: Mapped[TenantModel] = relationship(back_populates="runs")
    transitions: Mapped[list[TransitionModel]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="TransitionModel.created_at",
    )


class TransitionModel(Base):
    """One immutable entry in a run's audit trail.

    Append-only: rows are never updated or deleted while a run lives. This table
    is the literal answer to "why did the Creative Director reject this?" — each
    rejection persists here with its notes.
    """

    __tablename__ = "run_transitions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_state: Mapped[WorkflowState] = mapped_column(
        SAEnum(WorkflowState, name="workflow_state", native_enum=False, length=48),
        nullable=False,
    )
    to_state: Mapped[WorkflowState] = mapped_column(
        SAEnum(WorkflowState, name="workflow_state", native_enum=False, length=48),
        nullable=False,
    )
    event: Mapped[TransitionEvent] = mapped_column(
        SAEnum(TransitionEvent, name="transition_event", native_enum=False, length=24),
        nullable=False,
    )
    agent_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped[RunModel] = relationship(back_populates="transitions")
