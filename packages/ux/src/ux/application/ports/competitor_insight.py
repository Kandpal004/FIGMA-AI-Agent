"""The Competitor insight port — optional competitive UX-pattern signals from Phase 5.

Supplies neutral :class:`RawSignal` s about the competitive set's UX patterns and
conventions, so the strategy can honour familiar patterns (Jakob's Law) and differentiate
deliberately. Optional: a null adapter is valid when no competitor intelligence is
available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext

__all__ = ["CompetitorInsightPort"]


@runtime_checkable
class CompetitorInsightPort(Protocol):
    """Gathers competitor UX signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return competitor-derived signals for a project (may be empty)."""
        ...
