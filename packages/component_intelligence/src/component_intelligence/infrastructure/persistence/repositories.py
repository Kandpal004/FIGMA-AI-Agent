"""SQLAlchemy implementation of the specification repository.

Persists a specification as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from component_intelligence.domain.report.report import ComponentCompositionSpecification
from component_intelligence.domain.shared.ids import (
    ComponentSpecId,
    ComponentSpecLineageId,
)
from component_intelligence.infrastructure.persistence import codec
from component_intelligence.infrastructure.persistence.models import (
    ComponentSpecificationModel,
)

__all__ = ["SqlAlchemySpecificationRepository"]


class SqlAlchemySpecificationRepository:
    """Database-backed :class:`ComponentSpecificationRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, specification: ComponentCompositionSpecification) -> None:
        document = codec.to_document(specification)
        model = await self._session.get(ComponentSpecificationModel, specification.id.value)
        if model is None:
            self._session.add(
                ComponentSpecificationModel(
                    id=specification.id.value,
                    lineage_id=specification.lineage_id.value,
                    version=specification.version,
                    project_id=specification.project_id,
                    component_count=specification.component_count(),
                    included_count=specification.included_count(),
                    overall_score=specification.quality.overall_score.value,
                    document=document,
                    created_at=specification.created_at,
                )
            )
        else:
            model.version = specification.version
            model.included_count = specification.included_count()
            model.overall_score = specification.quality.overall_score.value
            model.document = document

    async def get(
        self, specification_id: ComponentSpecId
    ) -> ComponentCompositionSpecification:
        model = await self._session.get(ComponentSpecificationModel, specification_id.value)
        if model is None:
            raise NotFoundError(
                f"Specification {specification_id} not found.",
                details={"specification_id": str(specification_id)},
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: ComponentSpecLineageId
    ) -> ComponentCompositionSpecification:
        stmt = (
            select(ComponentSpecificationModel)
            .where(ComponentSpecificationModel.lineage_id == lineage_id.value)
            .order_by(ComponentSpecificationModel.version.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalars().first()
        if model is None:
            raise NotFoundError(
                f"No specifications for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return codec.from_document(model.document)

    async def history(
        self, lineage_id: ComponentSpecLineageId
    ) -> Sequence[ComponentCompositionSpecification]:
        stmt = (
            select(ComponentSpecificationModel)
            .where(ComponentSpecificationModel.lineage_id == lineage_id.value)
            .order_by(ComponentSpecificationModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
