"""The Wireframe input port (Phase 12) — the primary subject signals.

Supplies neutral :class:`RawSignal` s derived from the wireframe plan under review — pages,
sections, blocks, components, trust and conversion structure, approvals — so the Creative
Director reviews the actual plan. The infrastructure adapter imports Phase 12 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["WireframeInputPort"]


@runtime_checkable
class WireframeInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
