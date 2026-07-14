"""SQLAlchemy implementation of the IA report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from ia.domain.report.report import IAReport
from ia.domain.shared.ids import IAReportId, IAReportLineageId
from ia.infrastructure.persistence import codec
from ia.infrastructure.persistence.models import IAReportModel

__all__ = ["SqlAlchemyIAReportRepository"]


class SqlAlchemyIAReportRepository:
    """Database-backed :class:`IAReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: IAReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(IAReportModel, report.id.value)
        if model is None:
            self._session.add(
                IAReportModel(
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

    async def get(self, report_id: IAReportId) -> IAReport:
        model = await self._session.get(IAReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(self, lineage_id: IAReportLineageId) -> IAReport:
        stmt = (
            select(IAReportModel)
            .where(IAReportModel.lineage_id == lineage_id.value)
            .order_by(IAReportModel.version.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalars().first()
        if model is None:
            raise NotFoundError(
                f"No reports for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return codec.from_document(model.document)

    async def history(self, lineage_id: IAReportLineageId) -> Sequence[IAReport]:
        stmt = (
            select(IAReportModel)
            .where(IAReportModel.lineage_id == lineage_id.value)
            .order_by(IAReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
