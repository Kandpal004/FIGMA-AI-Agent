"""SQLAlchemy implementation of the model repository.

Persists a model as its codec document plus indexed columns, and reconstructs it (re-validated) on
load. Operates on an injected session; no ORM object escapes. Imports SQLAlchemy but no Figma SDK,
MCP client, or HTTP library.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.shared.ids import (
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
)
from figma_design.infrastructure.persistence import codec
from figma_design.infrastructure.persistence.models import FigmaDesignModelRow

__all__ = ["SqlAlchemyModelRepository"]


class SqlAlchemyModelRepository:
    """Database-backed :class:`FigmaModelRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, model: FigmaDesignModel) -> None:
        document = codec.to_document(model)
        row = await self._session.get(FigmaDesignModelRow, model.id.value)
        if row is None:
            self._session.add(
                FigmaDesignModelRow(
                    id=model.id.value,
                    lineage_id=model.lineage_id.value,
                    version=model.version,
                    project_id=model.project_id,
                    page_count=model.page_count(),
                    node_count=model.node_count(),
                    overall_score=model.quality.overall_score.value,
                    document=document,
                    created_at=model.created_at,
                )
            )
        else:
            row.version = model.version
            row.page_count = model.page_count()
            row.node_count = model.node_count()
            row.overall_score = model.quality.overall_score.value
            row.document = document

    async def get(self, model_id: FigmaDesignModelId) -> FigmaDesignModel:
        row = await self._session.get(FigmaDesignModelRow, model_id.value)
        if row is None:
            raise NotFoundError(
                f"Model {model_id} not found.", details={"model_id": str(model_id)}
            )
        return codec.from_document(row.document)

    async def latest(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> FigmaDesignModel:
        stmt = (
            select(FigmaDesignModelRow)
            .where(FigmaDesignModelRow.lineage_id == lineage_id.value)
            .order_by(FigmaDesignModelRow.version.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalars().first()
        if row is None:
            raise NotFoundError(
                f"No models for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return codec.from_document(row.document)

    async def history(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> Sequence[FigmaDesignModel]:
        stmt = (
            select(FigmaDesignModelRow)
            .where(FigmaDesignModelRow.lineage_id == lineage_id.value)
            .order_by(FigmaDesignModelRow.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(r.document) for r in rows]
