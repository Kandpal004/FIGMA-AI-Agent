"""The Phase 12 Wireframe Planning port — grounds layout, grid, and breakpoint tokens.

Supplies neutral :class:`RawSignal` s derived from the wireframe plan (layout structure, grid
intent, responsive breakpoints). The infrastructure adapter imports that engine and translates;
the design-system domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["WireframeInputPort"]


@runtime_checkable
class WireframeInputPort(Protocol):
    """Gathers wireframe-planning signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
