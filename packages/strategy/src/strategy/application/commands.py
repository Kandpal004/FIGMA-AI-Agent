"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from strategy.application.request import StrategyRequest
from strategy.domain.shared.ids import StrategyReportLineageId

__all__ = ["BuildStrategy"]


@dataclass(frozen=True, slots=True)
class BuildStrategy:
    """Build a business strategy for a request.

    Attributes:
        request: What to build a strategy for.
        lineage_id: The report lineage to append a new version to; ``None`` starts a
            fresh lineage.
    """

    request: StrategyRequest
    lineage_id: StrategyReportLineageId | None = None
