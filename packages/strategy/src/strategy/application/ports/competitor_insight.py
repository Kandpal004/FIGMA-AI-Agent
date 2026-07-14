"""The Competitor insight port — intelligence from the Phase-5 Competitor Engine.

Supplies competitor patterns, benchmark posture, and positioning signals as neutral
:class:`RawInsight` s, so strategy can be sharpened against the competitive set. The
infrastructure adapter imports Phase 5 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from strategy.application.contracts import RawInsight
from strategy.domain.context.context import ProjectContext

__all__ = ["CompetitorInsightPort"]


@runtime_checkable
class CompetitorInsightPort(Protocol):
    """Gathers competitor intelligence as neutral insights."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        """Return competitor-derived insights for a project (may be empty)."""
        ...
