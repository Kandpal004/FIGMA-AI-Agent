"""SQLAlchemy implementation of the wireframe plan repository.

Persists a plan as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from wireframe.domain.report.report import WireframePlan
from wireframe.domain.shared.ids import WireframePlanId, WireframePlanLineageId
from wireframe.infrastructure.persistence import codec
from wireframe.infrastructure.persistence.models import WireframePlanModel

__all__ = ["SqlAlchemyWireframePlanRepository"]


class SqlAlchemyWireframePlanRepository:
    """Database-backed :class:`WireframePlanRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, plan: WireframePlan) -> None:
        document = codec.to_document(plan)
        model = await self._session.get(WireframePlanModel, plan.id.value)
        if model is None:
            self._session.add(
                WireframePlanModel(
                    id=plan.id.value,
                    lineage_id=plan.lineage_id.value,
                    version=plan.version,
                    project_id=plan.project_id,
                    page_count=plan.page_count(),
                    section_count=plan.section_count(),
                    overall_score=plan.quality.overall_score.value,
                    document=document,
                    created_at=plan.created_at,
                )
            )
        else:
            model.version = plan.version
            model.page_count = plan.page_count()
            model.section_count = plan.section_count()
            model.overall_score = plan.quality.overall_score.value
            model.document = document

    async def get(self, plan_id: WireframePlanId) -> WireframePlan:
        model = await self._session.get(WireframePlanModel, plan_id.value)
        if model is None:
            raise NotFoundError(
                f"Plan {plan_id} not found.", details={"plan_id": str(plan_id)}
            )
        return codec.from_document(model.document)

    async def latest(self, lineage_id: WireframePlanLineageId) -> WireframePlan:
        stmt = (
            select(WireframePlanModel)
            .where(WireframePlanModel.lineage_id == lineage_id.value)
            .order_by(WireframePlanModel.version.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalars().first()
        if model is None:
            raise NotFoundError(
                f"No plans for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return codec.from_document(model.document)

    async def history(self, lineage_id: WireframePlanLineageId) -> Sequence[WireframePlan]:
        stmt = (
            select(WireframePlanModel)
            .where(WireframePlanModel.lineage_id == lineage_id.value)
            .order_by(WireframePlanModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
