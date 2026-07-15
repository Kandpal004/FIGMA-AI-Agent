"""SQLAlchemy implementation of the specification repository.

Persists a specification as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from design_system.domain.report.report import DesignSystemSpecification
from design_system.domain.shared.ids import (
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
)
from design_system.infrastructure.persistence import codec
from design_system.infrastructure.persistence.models import (
    DesignSystemSpecificationModel,
)

__all__ = ["SqlAlchemySpecificationRepository"]


class SqlAlchemySpecificationRepository:
    """Database-backed :class:`DesignSystemSpecificationRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, specification: DesignSystemSpecification) -> None:
        document = codec.to_document(specification)
        model = await self._session.get(
            DesignSystemSpecificationModel, specification.id.value
        )
        if model is None:
            self._session.add(
                DesignSystemSpecificationModel(
                    id=specification.id.value,
                    lineage_id=specification.lineage_id.value,
                    version=specification.version,
                    project_id=specification.project_id,
                    token_count=specification.token_count(),
                    component_count=specification.component_count(),
                    overall_score=specification.quality.overall_score.value,
                    document=document,
                    created_at=specification.created_at,
                )
            )
        else:
            model.version = specification.version
            model.token_count = specification.token_count()
            model.component_count = specification.component_count()
            model.overall_score = specification.quality.overall_score.value
            model.document = document

    async def get(
        self, specification_id: DesignSystemSpecId
    ) -> DesignSystemSpecification:
        model = await self._session.get(
            DesignSystemSpecificationModel, specification_id.value
        )
        if model is None:
            raise NotFoundError(
                f"Specification {specification_id} not found.",
                details={"specification_id": str(specification_id)},
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: DesignSystemSpecLineageId
    ) -> DesignSystemSpecification:
        stmt = (
            select(DesignSystemSpecificationModel)
            .where(DesignSystemSpecificationModel.lineage_id == lineage_id.value)
            .order_by(DesignSystemSpecificationModel.version.desc())
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
        self, lineage_id: DesignSystemSpecLineageId
    ) -> Sequence[DesignSystemSpecification]:
        stmt = (
            select(DesignSystemSpecificationModel)
            .where(DesignSystemSpecificationModel.lineage_id == lineage_id.value)
            .order_by(DesignSystemSpecificationModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
