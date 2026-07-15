"""The Phase 12 Wireframe Planning port — the primary driver of page/section order.

Supplies neutral :class:`RawSignal` s derived from the wireframe plan (the pages, their sections,
and the intended order). The infrastructure adapter imports that engine and translates; the
orchestrator domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["WireframeInputPort"]


@runtime_checkable
class WireframeInputPort(Protocol):
    """Gathers wireframe-planning signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
