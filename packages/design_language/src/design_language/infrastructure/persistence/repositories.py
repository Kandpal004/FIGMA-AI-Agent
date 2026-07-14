"""SQLAlchemy implementation of the specification repository.

Persists a specification as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from design_language.domain.report.report import DesignLanguageSpecification
from design_language.domain.shared.ids import (
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
)
from design_language.infrastructure.persistence import codec
from design_language.infrastructure.persistence.models import (
    DesignLanguageSpecificationModel,
)

__all__ = ["SqlAlchemySpecificationRepository"]


class SqlAlchemySpecificationRepository:
    """Database-backed :class:`DesignLanguageSpecificationRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, specification: DesignLanguageSpecification) -> None:
        document = codec.to_document(specification)
        model = await self._session.get(
            DesignLanguageSpecificationModel, specification.id.value
        )
        if model is None:
            self._session.add(
                DesignLanguageSpecificationModel(
                    id=specification.id.value,
                    lineage_id=specification.lineage_id.value,
                    version=specification.version,
                    project_id=specification.project_id,
                    industry=specification.industry.value,
                    archetype=specification.language_selection.archetype.value,
                    luxury_level=int(specification.visual_dna.luxury_level),
                    minimalism_level=int(specification.visual_dna.minimalism_level),
                    overall_score=specification.quality.overall_score.value,
                    document=document,
                    created_at=specification.created_at,
                )
            )
        else:
            model.version = specification.version
            model.overall_score = specification.quality.overall_score.value
            model.document = document

    async def get(
        self, specification_id: DesignLanguageSpecId
    ) -> DesignLanguageSpecification:
        model = await self._session.get(
            DesignLanguageSpecificationModel, specification_id.value
        )
        if model is None:
            raise NotFoundError(
                f"Specification {specification_id} not found.",
                details={"specification_id": str(specification_id)},
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: DesignLanguageSpecLineageId
    ) -> DesignLanguageSpecification:
        stmt = (
            select(DesignLanguageSpecificationModel)
            .where(DesignLanguageSpecificationModel.lineage_id == lineage_id.value)
            .order_by(DesignLanguageSpecificationModel.version.desc())
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
        self, lineage_id: DesignLanguageSpecLineageId
    ) -> Sequence[DesignLanguageSpecification]:
        stmt = (
            select(DesignLanguageSpecificationModel)
            .where(DesignLanguageSpecificationModel.lineage_id == lineage_id.value)
            .order_by(DesignLanguageSpecificationModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
