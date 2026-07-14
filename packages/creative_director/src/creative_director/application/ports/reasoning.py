"""The Reasoning input port (Phase 4).

Supplies neutral :class:`RawSignal` s derived from the reasoning engine, so rulings can
reference derived rationale. The infrastructure adapter imports Phase 4 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["ReasoningPort"]


@runtime_checkable
class ReasoningPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
