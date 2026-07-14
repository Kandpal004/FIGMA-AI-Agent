"""SQLAlchemy ORM model — the durable shape of a produced report.

A report is stored as one row: the full aggregate as a JSON ``document`` (via the
codec) plus indexed, queryable columns (lineage, version, industry, confidence, risk
level). Loading and saving are whole-aggregate. One table holds every version of
every lineage, which is exactly what the versioned-reports model needs.

Schema migrations are owned by Alembic in a later phase; ``create_all`` suffices for
local bring-up and tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "ReportModel"]


class Base(DeclarativeBase):
    """Declarative base for the Competitor Intelligence ORM models."""


class ReportModel(Base):
    """One produced competitor intelligence report version."""

    __tablename__ = "competitive_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    lineage_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    industry: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    is_actionable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    document: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
