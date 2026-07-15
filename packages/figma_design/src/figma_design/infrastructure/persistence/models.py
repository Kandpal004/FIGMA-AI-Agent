"""SQLAlchemy ORM model — the durable shape of a produced model.

A Figma design model is stored as one row: the full aggregate as a JSON ``document`` (via the
codec) plus indexed, queryable columns (lineage, version, project, counts, score). Loading and
saving are whole-aggregate. One table holds every version of every lineage.

Schema migrations are owned by Alembic in a later phase; ``create_all`` suffices for local
bring-up and tests. This module imports SQLAlchemy (an infrastructure concern) but no Figma SDK,
MCP client, or HTTP library.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "FigmaDesignModelRow"]


class Base(DeclarativeBase):
    """Declarative base for the Figma Design ORM models."""


class FigmaDesignModelRow(Base):
    """One produced Figma design model version."""

    __tablename__ = "figma_design_models"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    lineage_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    project_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    document: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
