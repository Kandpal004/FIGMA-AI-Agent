"""The Competitor-Intelligence input port (Phase 5).

Supplies neutral :class:`RawSignal` s derived from competitor intelligence, so rulings can
reference the competitive landscape. The infrastructure adapter imports Phase 5 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["CompetitorInsightPort"]


@runtime_checkable
class CompetitorInsightPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
