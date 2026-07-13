"""SQLAlchemy ORM model — the durable shape of the knowledge corpus.

One table holds every version of every entry (keyed by version id), which is
exactly what the immutable, lineage-based versioning model needs: history is never
overwritten, and the current view is the highest ``ACTIVE`` version per lineage.
An entry's value objects and graph edges are stored as JSON on the row, because
an entry is always loaded and saved whole (it is a small, self-contained
aggregate).

Multi-tenancy rides on a nullable ``tenant_id`` (``NULL`` = global), realising the
global-base + tenant-override scope. Schema migrations are owned by Alembic in a
later phase; ``create_all`` on this metadata suffices for local bring-up and tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "KnowledgeEntryModel"]


class Base(DeclarativeBase):
    """Declarative base for the Knowledge Engine's ORM models."""


class KnowledgeEntryModel(Base):
    """One immutable version of a knowledge entry."""

    __tablename__ = "knowledge_entries"

    # Identity / versioning
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)  # entry version id
    knowledge_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Scope (NULL tenant = global)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    # Classification
    category: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Provenance / weighting / lifecycle
    source: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)

    # Structured facets / graph / citations (JSON-encoded value objects)
    applicability: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    relations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    references: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
