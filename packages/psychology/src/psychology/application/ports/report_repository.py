"""The Report repository port — persistence for produced psychology reports.

Reports are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete
implementations; tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from psychology.domain.report.report import CustomerPsychologyReport
from psychology.domain.shared.ids import PsychologyReportId, PsychologyReportLineageId

__all__ = ["PsychologyReportRepository"]


@runtime_checkable
class PsychologyReportRepository(Protocol):
    """Persists and loads :class:`CustomerPsychologyReport` versions."""

    async def save(self, report: CustomerPsychologyReport) -> None:
        """Persist a report version (insert or update by id)."""
        ...

    async def get(self, report_id: PsychologyReportId) -> CustomerPsychologyReport:
        """Return a report by id.

        Raises:
            NotFoundError: If no such report exists.
        """
        ...

    async def latest(
        self, lineage_id: PsychologyReportLineageId
    ) -> CustomerPsychologyReport:
        """Return the highest-version report of a lineage.

        Raises:
            NotFoundError: If the lineage has no reports.
        """
        ...

    async def history(
        self, lineage_id: PsychologyReportLineageId
    ) -> Sequence[CustomerPsychologyReport]:
        """Return every version of a lineage, oldest first."""
        ...
