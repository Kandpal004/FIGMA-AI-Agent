"""SQLAlchemy implementation of the research report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from research.domain.report.report import ResearchReport
from research.domain.shared.ids import ResearchReportId, ResearchReportLineageId
from research.infrastructure.persistence import codec
from research.infrastructure.persistence.models import ResearchReportModel

__all__ = ["SqlAlchemyResearchReportRepository"]


class SqlAlchemyResearchReportRepository:
    """Database-backed :class:`ResearchReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: ResearchReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(ResearchReportModel, report.id.value)
        if model is None:
            self._session.add(
                ResearchReportModel(
                    id=report.id.value,
                    lineage_id=report.lineage_id.value,
                    version=report.version,
                    project_id=report.project_id,
                    goal=report.goal,
                    quality_score=report.quality.quality_score.value,
                    confidence=report.quality.confidence.value,
                    document=document,
                    created_at=report.created_at,
                )
            )
        else:
            model.version = report.version
            model.quality_score = report.quality.quality_score.value
            model.confidence = report.quality.confidence.value
            model.document = document

    async def get(self, report_id: ResearchReportId) -> ResearchReport:
        model = await self._session.get(ResearchReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(self, lineage_id: ResearchReportLineageId) -> ResearchReport:
        stmt = (
            select(ResearchReportModel)
            .where(ResearchReportModel.lineage_id == lineage_id.value)
            .order_by(ResearchReportModel.version.desc())
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
        self, lineage_id: ResearchReportLineageId
    ) -> Sequence[ResearchReport]:
        stmt = (
            select(ResearchReportModel)
            .where(ResearchReportModel.lineage_id == lineage_id.value)
            .order_by(ResearchReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
