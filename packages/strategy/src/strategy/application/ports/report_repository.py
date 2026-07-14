"""The Report repository port — persistence for produced strategy reports.

Reports are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete
implementations; tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from strategy.domain.report.report import BusinessStrategyReport
from strategy.domain.shared.ids import StrategyReportId, StrategyReportLineageId

__all__ = ["StrategyReportRepository"]


@runtime_checkable
class StrategyReportRepository(Protocol):
    """Persists and loads :class:`BusinessStrategyReport` versions."""

    async def save(self, report: BusinessStrategyReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: StrategyReportId) -> BusinessStrategyReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(
        self, lineage_id: StrategyReportLineageId
    ) -> BusinessStrategyReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(
        self, lineage_id: StrategyReportLineageId
    ) -> Sequence[BusinessStrategyReport]:
        """Return every version of a lineage, oldest first."""
        ...
