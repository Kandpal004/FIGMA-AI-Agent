"""The Report repository port — persistence for produced research reports.

Reports are versioned; the repository stores each version and can return the latest
by lineage and the full history. The infrastructure layer supplies concrete
implementations; tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from research.domain.report.report import ResearchReport
from research.domain.shared.ids import ResearchReportId, ResearchReportLineageId

__all__ = ["ResearchReportRepository"]


@runtime_checkable
class ResearchReportRepository(Protocol):
    """Persists and loads :class:`ResearchReport` versions."""

    async def save(self, report: ResearchReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: ResearchReportId) -> ResearchReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(self, lineage_id: ResearchReportLineageId) -> ResearchReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(
        self, lineage_id: ResearchReportLineageId
    ) -> Sequence[ResearchReport]:
        """Return every version of a lineage, oldest first."""
        ...
