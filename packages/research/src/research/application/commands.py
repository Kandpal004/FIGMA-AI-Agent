"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from research.domain.shared.ids import ResearchReportLineageId
from research.domain.source.request import ResearchRequest

__all__ = ["Research"]


@dataclass(frozen=True, slots=True)
class Research:
    """Run research for a request.

    Attributes:
        request: What to research.
        lineage_id: The report lineage to append a new version to; ``None`` starts a
            fresh lineage.
    """

    request: ResearchRequest
    lineage_id: ResearchReportLineageId | None = None
