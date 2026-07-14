"""The Reasoning port — optional reasoning conclusions from Phase 4.

Supplies neutral :class:`RawSignal` s derived from the platform's structured inferences.
Optional: a null adapter is valid when no reasoning is available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from brand.application.contracts import RawSignal
from brand.domain.context.context import ProjectContext

__all__ = ["ReasoningPort"]


@runtime_checkable
class ReasoningPort(Protocol):
    """Gathers reasoning conclusions as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return reasoning-derived signals for a project (may be empty)."""
        ...
