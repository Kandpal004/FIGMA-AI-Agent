"""The Competitor-Intelligence input port (Phase 5).

Supplies neutral :class:`RawSignal` s derived from competitor intelligence, so planning
decisions can reference the competitive landscape. The infrastructure adapter imports Phase 5
and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from wireframe.application.contracts import RawSignal
from wireframe.domain.context.context import ProjectContext

__all__ = ["CompetitorInsightPort"]


@runtime_checkable
class CompetitorInsightPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
