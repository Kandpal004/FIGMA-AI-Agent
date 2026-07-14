"""The UX-strategy input port (Phase 10).

Supplies neutral :class:`RawSignal` s derived from the UX strategy — page objectives, CTAs,
navigation, friction, and journey intent — so section order and interaction requirements are
grounded in the experience strategy. The infrastructure adapter imports Phase 10 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from wireframe.application.contracts import RawSignal
from wireframe.domain.context.context import ProjectContext

__all__ = ["UXInputPort"]


@runtime_checkable
class UXInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
