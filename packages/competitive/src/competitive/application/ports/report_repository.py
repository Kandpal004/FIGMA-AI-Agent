"""The Report repository port — persistence for produced intelligence reports.

Reports are versioned; the repository stores each version and can return the latest
by lineage and the full history. The infrastructure layer supplies concrete
implementations; tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from competitive.domain.report.report import CompetitorIntelligenceReport
from competitive.domain.shared.ids import ReportId, ReportLineageId

__all__ = ["ReportRepository"]


@runtime_checkable
class ReportRepository(Protocol):
    """Persists and loads :class:`CompetitorIntelligenceReport` versions."""

    async def save(self, report: CompetitorIntelligenceReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: ReportId) -> CompetitorIntelligenceReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(self, lineage_id: ReportLineageId) -> CompetitorIntelligenceReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(
        self, lineage_id: ReportLineageId
    ) -> Sequence[CompetitorIntelligenceReport]:
        """Return every version of a lineage, oldest first."""
        ...
