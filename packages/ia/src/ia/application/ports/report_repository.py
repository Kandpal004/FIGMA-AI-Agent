"""The Report repository port — persistence for produced IA reports.

Reports are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete implementations;
tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ia.domain.report.report import IAReport
from ia.domain.shared.ids import IAReportId, IAReportLineageId

__all__ = ["IAReportRepository"]


@runtime_checkable
class IAReportRepository(Protocol):
    """Persists and loads :class:`IAReport` versions."""

    async def save(self, report: IAReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: IAReportId) -> IAReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(self, lineage_id: IAReportLineageId) -> IAReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(self, lineage_id: IAReportLineageId) -> Sequence[IAReport]:
        """Return every version of a lineage, oldest first."""
        ...
