"""SQLAlchemy implementation of the strategy report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from strategy.domain.report.report import BusinessStrategyReport
from strategy.domain.shared.ids import StrategyReportId, StrategyReportLineageId
from strategy.infrastructure.persistence import codec
from strategy.infrastructure.persistence.models import StrategyReportModel

__all__ = ["SqlAlchemyStrategyReportRepository"]


class SqlAlchemyStrategyReportRepository:
    """Database-backed :class:`StrategyReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: BusinessStrategyReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(StrategyReportModel, report.id.value)
        if model is None:
            self._session.add(
                StrategyReportModel(
                    id=report.id.value,
                    lineage_id=report.lineage_id.value,
                    version=report.version,
                    project_id=report.project_id,
                    tier=report.tier.value,
                    overall_score=report.quality.overall_score.value,
                    document=document,
                    created_at=report.created_at,
                )
            )
        else:
            model.version = report.version
            model.tier = report.tier.value
            model.overall_score = report.quality.overall_score.value
            model.document = document

    async def get(self, report_id: StrategyReportId) -> BusinessStrategyReport:
        model = await self._session.get(StrategyReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: StrategyReportLineageId
    ) -> BusinessStrategyReport:
        stmt = (
            select(StrategyReportModel)
            .where(StrategyReportModel.lineage_id == lineage_id.value)
            .order_by(StrategyReportModel.version.desc())
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
        self, lineage_id: StrategyReportLineageId
    ) -> Sequence[BusinessStrategyReport]:
        stmt = (
            select(StrategyReportModel)
            .where(StrategyReportModel.lineage_id == lineage_id.value)
            .order_by(StrategyReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
