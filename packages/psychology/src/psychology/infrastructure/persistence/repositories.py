"""SQLAlchemy implementation of the psychology report repository.

Persists a report as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from psychology.domain.report.report import CustomerPsychologyReport
from psychology.domain.shared.ids import PsychologyReportId, PsychologyReportLineageId
from psychology.infrastructure.persistence import codec
from psychology.infrastructure.persistence.models import PsychologyReportModel

__all__ = ["SqlAlchemyPsychologyReportRepository"]


class SqlAlchemyPsychologyReportRepository:
    """Database-backed :class:`PsychologyReportRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: CustomerPsychologyReport) -> None:
        document = codec.to_document(report)
        model = await self._session.get(PsychologyReportModel, report.id.value)
        if model is None:
            self._session.add(
                PsychologyReportModel(
                    id=report.id.value,
                    lineage_id=report.lineage_id.value,
                    version=report.version,
                    project_id=report.project_id,
                    awareness_level=report.awareness.value,
                    sophistication_level=report.sophistication.value,
                    overall_score=report.quality.overall_score.value,
                    document=document,
                    created_at=report.created_at,
                )
            )
        else:
            model.version = report.version
            model.awareness_level = report.awareness.value
            model.sophistication_level = report.sophistication.value
            model.overall_score = report.quality.overall_score.value
            model.document = document

    async def get(self, report_id: PsychologyReportId) -> CustomerPsychologyReport:
        model = await self._session.get(PsychologyReportModel, report_id.value)
        if model is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: PsychologyReportLineageId
    ) -> CustomerPsychologyReport:
        stmt = (
            select(PsychologyReportModel)
            .where(PsychologyReportModel.lineage_id == lineage_id.value)
            .order_by(PsychologyReportModel.version.desc())
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
        self, lineage_id: PsychologyReportLineageId
    ) -> Sequence[CustomerPsychologyReport]:
        stmt = (
            select(PsychologyReportModel)
            .where(PsychologyReportModel.lineage_id == lineage_id.value)
            .order_by(PsychologyReportModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
