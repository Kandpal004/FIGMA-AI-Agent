"""SQLAlchemy implementation of the report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from competitive.domain.report.report import CompetitorIntelligenceReport
from competitive.domain.shared.ids import ReportId, ReportLineageId
from competitive.infrastructure.persistence import codec
from competitive.infrastructure.persistence.models import ReportModel

__all__ = ["SqlAlchemyReportRepository"]


class SqlAlchemyReportRepository:
    """Postgres-backed :class:`ReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: CompetitorIntelligenceReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(ReportModel, report.id.value)
        if model is None:
            self._session.add(
                ReportModel(
                    id=report.id.value,
                    lineage_id=report.lineage_id.value,
                    version=report.version,
                    industry=report.industry,
                    market=report.market,
                    country=report.country,
                    overall_confidence=report.confidence.value,
                    risk_level=report.risk_matrix.overall_level.value,
                    is_actionable=report.is_actionable,
                    document=document,
                    created_at=report.created_at,
                )
            )
        else:
            model.version = report.version
            model.overall_confidence = report.confidence.value
            model.risk_level = report.risk_matrix.overall_level.value
            model.is_actionable = report.is_actionable
            model.document = document

    async def get(self, report_id: ReportId) -> CompetitorIntelligenceReport:
        model = await self._session.get(ReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: ReportLineageId
    ) -> CompetitorIntelligenceReport:
        stmt = (
            select(ReportModel)
            .where(ReportModel.lineage_id == lineage_id.value)
            .order_by(ReportModel.version.desc())
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
        self, lineage_id: ReportLineageId
    ) -> Sequence[CompetitorIntelligenceReport]:
        stmt = (
            select(ReportModel)
            .where(ReportModel.lineage_id == lineage_id.value)
            .order_by(ReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
