"""The Reasoning port — conclusions from the Phase-4 Reasoning Engine.

Supplies derived reasoning conclusions as neutral :class:`RawInsight` s, so strategy
can rest on the platform's structured inferences rather than raw observation alone. The
infrastructure adapter imports Phase 4 and translates; a null adapter is valid when no
reasoning is available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from strategy.application.contracts import RawInsight
from strategy.domain.context.context import ProjectContext

__all__ = ["ReasoningPort"]


@runtime_checkable
class ReasoningPort(Protocol):
    """Gathers reasoning conclusions as neutral insights."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        """Return reasoning-derived insights for a project (may be empty)."""
        ...
