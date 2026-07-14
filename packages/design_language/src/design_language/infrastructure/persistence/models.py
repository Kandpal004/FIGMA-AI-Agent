"""SQLAlchemy ORM model — the durable shape of a produced specification.

A specification is stored as one row: the full aggregate as a JSON ``document`` (via the
codec) plus indexed, queryable columns (lineage, version, project, industry, archetype,
levels, score). Loading and saving are whole-aggregate. One table holds every version of every
lineage — exactly what the versioned-specifications model needs.

Schema migrations are owned by Alembic in a later phase; ``create_all`` suffices for local
bring-up and tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "DesignLanguageSpecificationModel"]


class Base(DeclarativeBase):
    """Declarative base for the Design Language ORM models."""


class DesignLanguageSpecificationModel(Base):
    """One produced design-language specification version."""

    __tablename__ = "design_language_specifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    lineage_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    project_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(40), nullable=False)
    archetype: Mapped[str] = mapped_column(String(40), nullable=False)
    luxury_level: Mapped[int] = mapped_column(Integer, nullable=False)
    minimalism_level: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    document: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
