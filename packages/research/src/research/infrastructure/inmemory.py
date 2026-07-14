"""In-memory persistence for the Research Engine.

A system clock and a dict-backed report store + unit of work, so the engine runs and
is tested with no external services. Semantics match the real SQLAlchemy adapters.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from research.application.ports.clock import Clock
from research.domain.report.report import ResearchReport
from research.domain.shared.ids import ResearchReportId, ResearchReportLineageId

__all__ = [
    "InMemoryReportRepository",
    "InMemoryUnitOfWork",
    "ReportStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ReportStorage:
    """Process-lifetime storage for produced reports."""

    def __init__(self) -> None:
        self.by_id: dict[ResearchReportId, ResearchReport] = {}
        self.by_lineage: dict[ResearchReportLineageId, list[ResearchReport]] = {}


class InMemoryReportRepository:
    """Dict-backed :class:`ResearchReportRepository`."""

    def __init__(self, storage: ReportStorage) -> None:
        self._storage = storage

    async def save(self, report: ResearchReport) -> None:
        self._storage.by_id[report.id] = report
        versions = self._storage.by_lineage.setdefault(report.lineage_id, [])
        versions[:] = [r for r in versions if r.id != report.id]
        versions.append(report)

    async def get(self, report_id: ResearchReportId) -> ResearchReport:
        report = self._storage.by_id.get(report_id)
        if report is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return report

    async def latest(self, lineage_id: ResearchReportLineageId) -> ResearchReport:
        versions = self._storage.by_lineage.get(lineage_id)
        if not versions:
            raise NotFoundError(
                f"No reports for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return max(versions, key=lambda r: r.version)

    async def history(
        self, lineage_id: ResearchReportLineageId
    ) -> Sequence[ResearchReport]:
        versions = self._storage.by_lineage.get(lineage_id, [])
        return sorted(versions, key=lambda r: r.version)


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage."""

    def __init__(self, storage: ReportStorage) -> None:
        self.reports = InMemoryReportRepository(storage)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def make_unit_of_work_factory(storage: ReportStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
