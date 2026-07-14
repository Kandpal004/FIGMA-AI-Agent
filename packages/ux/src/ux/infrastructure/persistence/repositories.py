"""SQLAlchemy implementation of the UX report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from ux.domain.report.report import UXStrategyReport
from ux.domain.shared.ids import UXReportId, UXReportLineageId
from ux.infrastructure.persistence import codec
from ux.infrastructure.persistence.models import UXReportModel

__all__ = ["SqlAlchemyUXReportRepository"]


class SqlAlchemyUXReportRepository:
    """Database-backed :class:`UXReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: UXStrategyReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(UXReportModel, report.id.value)
        if model is None:
            self._session.add(
                UXReportModel(
                    id=report.id.value,
                    lineage_id=report.lineage_id.value,
                    version=report.version,
                    project_id=report.project_id,
                    page_count=report.page_count(),
                    overall_score=report.quality.overall_score.value,
                    document=document,
                    created_at=report.created_at,
                )
            )
        else:
            model.version = report.version
            model.page_count = report.page_count()
            model.overall_score = report.quality.overall_score.value
            model.document = document

    async def get(self, report_id: UXReportId) -> UXStrategyReport:
        model = await self._session.get(UXReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(self, lineage_id: UXReportLineageId) -> UXStrategyReport:
        stmt = (
            select(UXReportModel)
            .where(UXReportModel.lineage_id == lineage_id.value)
            .order_by(UXReportModel.version.desc())
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
        self, lineage_id: UXReportLineageId
    ) -> Sequence[UXStrategyReport]:
        stmt = (
            select(UXReportModel)
            .where(UXReportModel.lineage_id == lineage_id.value)
            .order_by(UXReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
