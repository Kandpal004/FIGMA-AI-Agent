"""The Report repository port — persistence for produced brand strategy reports.

Reports are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete
implementations; tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from brand.domain.report.report import BrandStrategyReport
from brand.domain.shared.ids import BrandReportId, BrandReportLineageId

__all__ = ["BrandReportRepository"]


@runtime_checkable
class BrandReportRepository(Protocol):
    """Persists and loads :class:`BrandStrategyReport` versions."""

    async def save(self, report: BrandStrategyReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: BrandReportId) -> BrandStrategyReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(self, lineage_id: BrandReportLineageId) -> BrandStrategyReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(
        self, lineage_id: BrandReportLineageId
    ) -> Sequence[BrandStrategyReport]:
        """Return every version of a lineage, oldest first."""
        ...
