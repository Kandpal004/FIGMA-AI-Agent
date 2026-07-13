"""SQLAlchemy ORM model — the durable shape of a produced strategy.

A strategy is stored as one row: the full aggregate as a JSON ``document`` (via
the codec) plus a handful of indexed, queryable columns (project, section, page,
stance, overall confidence, risk level). Loading and saving are whole-aggregate,
matching how the domain treats it.

Schema migrations are owned by Alembic in a later phase; ``create_all`` on this
metadata suffices for local bring-up and tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "StrategyModel"]


class Base(DeclarativeBase):
    """Declarative base for the Reasoning Engine's ORM models."""


class StrategyModel(Base):
    """One produced design strategy."""

    __tablename__ = "reasoning_strategies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_type: Mapped[str] = mapped_column(String(48), nullable=False)
    stance: Mapped[str] = mapped_column(String(32), nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    is_actionable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    document: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
