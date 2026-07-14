"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from ia.application.request import IARequest
from ia.domain.shared.ids import IAReportLineageId

__all__ = ["BuildIA"]


@dataclass(frozen=True, slots=True)
class BuildIA:
    """Build an information architecture for a request.

    Attributes:
        request: What to build an IA for.
        lineage_id: The report lineage to append a new version to; ``None`` starts a fresh
            lineage.
    """

    request: IARequest
    lineage_id: IAReportLineageId | None = None
