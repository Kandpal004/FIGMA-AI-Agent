"""The UX-strategy input port (Phase 10).

Supplies neutral :class:`RawSignal` s derived from the UX strategy — goals, CTAs, friction,
journey intent — so UX-quality and conversion reviews are grounded. The infrastructure
adapter imports Phase 10 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["UXInputPort"]


@runtime_checkable
class UXInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
