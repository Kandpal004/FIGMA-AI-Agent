"""The Reasoning port — optional alignment with the active design strategy.

Per the approved decision, the Reasoning Engine (Phase 4) is an **optional** context
source: when wired, the engine consults it to align recommendations with the
current strategy (e.g. its stance and priority dimensions); when absent, the report
is produced from observations + Knowledge grounding alone. Knowledge remains the
mandatory evidence base; reasoning only enriches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.value_objects import CompetitorDimension

__all__ = ["ReasoningPort", "StrategyDigest"]


@dataclass(frozen=True, slots=True)
class StrategyDigest:
    """A lightweight digest of the active design strategy, for alignment.

    Attributes:
        stance: The strategy stance (e.g. ``"conversion_first"``).
        priority_dimensions: Dimensions the strategy emphasises (recommendations
            touching these are prioritised).
        notes: Optional free-text alignment notes.
    """

    stance: str = ""
    priority_dimensions: tuple[CompetitorDimension, ...] = ()
    notes: str = ""


@runtime_checkable
class ReasoningPort(Protocol):
    """Optionally supplies a digest of the active strategy for alignment."""

    async def digest(self, brief: CompetitiveBrief) -> StrategyDigest | None:
        """Return a strategy digest to align with, or ``None`` if unavailable."""
        ...
