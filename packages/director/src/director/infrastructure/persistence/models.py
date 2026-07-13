"""SQLAlchemy ORM models — the durable shape of the Director's aggregates.

These tables are the Postgres realisation of the domain aggregates and satisfy
Principle P4 (every workflow is stored in PostgreSQL) and P5 (auditable). The
design follows aggregate boundaries: a run and a project are each loaded and
saved *whole*, so their internal collections (a run's steps, a project's
sections) are stored as JSON on the aggregate row rather than as separate tables.
The append-only audit streams — decisions — and the memory records get their own
tables, since they are queried independently of any single aggregate.

Multi-tenancy is carried on every tenant-owned row (``tenant_id`` on projects;
runs and memory reach it through their project), consistent with ADR-0007.

Schema migrations are owned by Alembic in a later phase; :func:`create_all` on
this metadata suffices for local bring-up and tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

__all__ = [
    "Base",
    "DecisionModel",
    "MemoryRecordModel",
    "ProjectModel",
    "RunModel",
]


class Base(DeclarativeBase):
    """Declarative base for the Director's ORM models."""


class ProjectModel(Base):
    """A project aggregate; its sections are stored inline as JSON."""

    __tablename__ = "director_projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # [{"id","key","page_type","title"}, ...]
    sections: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    runs: Mapped[list[RunModel]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class RunModel(Base):
    """A workflow-run aggregate; its steps/brief/artifacts are stored inline."""

    __tablename__ = "director_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("director_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    workflow_key: Mapped[str] = mapped_column(String(120), nullable=False)
    workflow_version: Mapped[int] = mapped_column(Integer, nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    current_step_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(24), nullable=False)
    redesign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # [{"id","key","state","attempt_number","attempt_limit","rejection_notes","output_summary"}, ...]
    steps: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    brief: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    artifacts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped[ProjectModel] = relationship(back_populates="runs")


class DecisionModel(Base):
    """One immutable entry in the Director's reasoning log (append-only)."""

    __tablename__ = "director_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    step_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MemoryRecordModel(Base):
    """A durable memory record (structured recall)."""

    __tablename__ = "director_memory_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    section_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
