"""The Research input port (Phase 6).

Supplies neutral :class:`RawSignal` s derived from research evidence, so rulings can cite
primary findings. The infrastructure adapter imports Phase 6 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["ResearchInputPort"]


@runtime_checkable
class ResearchInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
