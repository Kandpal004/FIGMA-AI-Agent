"""The Report repository port — persistence for produced UX strategy reports.

Reports are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete implementations;
tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ux.domain.report.report import UXStrategyReport
from ux.domain.shared.ids import UXReportId, UXReportLineageId

__all__ = ["UXReportRepository"]


@runtime_checkable
class UXReportRepository(Protocol):
    """Persists and loads :class:`UXStrategyReport` versions."""

    async def save(self, report: UXStrategyReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: UXReportId) -> UXStrategyReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(self, lineage_id: UXReportLineageId) -> UXStrategyReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(
        self, lineage_id: UXReportLineageId
    ) -> Sequence[UXStrategyReport]:
        """Return every version of a lineage, oldest first."""
        ...
