"""The Phase 8 Brand Strategy port — grounds the visual/emphasis choices.

Supplies neutral :class:`RawSignal` s derived from the brand strategy (personality, tone). The
infrastructure adapter imports that engine and translates; the orchestrator domain never imports
it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["BrandInputPort"]


@runtime_checkable
class BrandInputPort(Protocol):
    """Gathers brand-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
