"""In-memory infrastructure for the Competitor Intelligence Engine.

Real, dependency-free implementations of every port, so the engine runs and is
tested with no external services: a static data source, a scriptable knowledge
advisor, a null reasoning port (the honest "no reasoning" default), an in-memory
report store and unit of work, and a system clock.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from competitive.application.ports.clock import Clock
from competitive.application.ports.knowledge_advisor import AdvisedPrinciple
from competitive.application.ports.reasoning import StrategyDigest
from competitive.domain.competitor.observation import ObservationSet
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.report.report import CompetitorIntelligenceReport
from competitive.domain.shared.ids import ReportId, ReportLineageId
from competitive.domain.shared.value_objects import CompetitorDimension

__all__ = [
    "InMemoryDataSource",
    "InMemoryKnowledgeAdvisor",
    "InMemoryReportRepository",
    "InMemoryUnitOfWork",
    "NullReasoningPort",
    "ReportStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class InMemoryDataSource:
    """A static data source returning a fixed observation set."""

    def __init__(self, observations: ObservationSet) -> None:
        self._observations = observations

    async def gather(self, brief: CompetitiveBrief) -> ObservationSet:
        return self._observations


class InMemoryKnowledgeAdvisor:
    """A scriptable advisor returning fixed principles per dimension."""

    def __init__(
        self,
        principles: Mapping[CompetitorDimension, Sequence[AdvisedPrinciple]] | None = None,
    ) -> None:
        self._principles: dict[CompetitorDimension, tuple[AdvisedPrinciple, ...]] = {
            dimension: tuple(items) for dimension, items in (principles or {}).items()
        }

    async def advise(
        self,
        dimension: CompetitorDimension,
        *,
        industry: str | None = None,
        market: str | None = None,
        contexts: Sequence[str] = (),
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[AdvisedPrinciple]:
        items = self._principles.get(dimension, ())
        return items[:limit] if limit is not None else items


class NullReasoningPort:
    """A reasoning port that supplies no digest (reasoning not wired)."""

    async def digest(self, brief: CompetitiveBrief) -> StrategyDigest | None:
        return None


class ReportStorage:
    """Process-lifetime storage for produced reports."""

    def __init__(self) -> None:
        self.by_id: dict[ReportId, CompetitorIntelligenceReport] = {}
        self.by_lineage: dict[ReportLineageId, list[CompetitorIntelligenceReport]] = {}


class InMemoryReportRepository:
    """Dict-backed :class:`ReportRepository`."""

    def __init__(self, storage: ReportStorage) -> None:
        self._storage = storage

    async def save(self, report: CompetitorIntelligenceReport) -> None:
        self._storage.by_id[report.id] = report
        versions = self._storage.by_lineage.setdefault(report.lineage_id, [])
        versions[:] = [r for r in versions if r.id != report.id]
        versions.append(report)

    async def get(self, report_id: ReportId) -> CompetitorIntelligenceReport:
        report = self._storage.by_id.get(report_id)
        if report is None:
            raise NotFoundError(
                f"Report {report_id} not found.", details={"report_id": str(report_id)}
            )
        return report

    async def latest(
        self, lineage_id: ReportLineageId
    ) -> CompetitorIntelligenceReport:
        versions = self._storage.by_lineage.get(lineage_id)
        if not versions:
            raise NotFoundError(
                f"No reports for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return max(versions, key=lambda r: r.version)

    async def history(
        self, lineage_id: ReportLineageId
    ) -> Sequence[CompetitorIntelligenceReport]:
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
