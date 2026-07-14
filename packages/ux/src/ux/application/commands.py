"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from ux.application.request import UXRequest
from ux.domain.shared.ids import UXReportLineageId

__all__ = ["BuildUXStrategy"]


@dataclass(frozen=True, slots=True)
class BuildUXStrategy:
    """Build a UX strategy for a request.

    Attributes:
        request: What to build a UX strategy for.
        lineage_id: The report lineage to append a new version to; ``None`` starts a fresh
            lineage.
    """

    request: UXRequest
    lineage_id: UXReportLineageId | None = None
