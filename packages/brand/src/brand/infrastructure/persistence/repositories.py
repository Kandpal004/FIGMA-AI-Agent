"""SQLAlchemy implementation of the brand report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from brand.domain.report.report import BrandStrategyReport
from brand.domain.shared.ids import BrandReportId, BrandReportLineageId
from brand.infrastructure.persistence import codec
from brand.infrastructure.persistence.models import BrandReportModel

__all__ = ["SqlAlchemyBrandReportRepository"]


class SqlAlchemyBrandReportRepository:
    """Database-backed :class:`BrandReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: BrandStrategyReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(BrandReportModel, report.id.value)
        if model is None:
            self._session.add(
                BrandReportModel(
                    id=report.id.value,
                    lineage_id=report.lineage_id.value,
                    version=report.version,
                    project_id=report.project_id,
                    primary_category=report.primary_category.value,
                    archetype=report.archetype.value,
                    overall_score=report.quality.overall_score.value,
                    document=document,
                    created_at=report.created_at,
                )
            )
        else:
            model.version = report.version
            model.primary_category = report.primary_category.value
            model.archetype = report.archetype.value
            model.overall_score = report.quality.overall_score.value
            model.document = document

    async def get(self, report_id: BrandReportId) -> BrandStrategyReport:
        model = await self._session.get(BrandReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(self, lineage_id: BrandReportLineageId) -> BrandStrategyReport:
        stmt = (
            select(BrandReportModel)
            .where(BrandReportModel.lineage_id == lineage_id.value)
            .order_by(BrandReportModel.version.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalars().first()
        if model is None:
            raise NotFoundError(
                f"No reports for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return codec.from_document(model.document)

    async def history(
        self, lineage_id: BrandReportLineageId
    ) -> Sequence[BrandStrategyReport]:
        stmt = (
            select(BrandReportModel)
            .where(BrandReportModel.lineage_id == lineage_id.value)
            .order_by(BrandReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
