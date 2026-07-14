"""The Brand-Strategy input port (Phase 8).

Supplies neutral :class:`RawSignal` s derived from the brand guidelines — archetype, tone,
positioning — so brand-alignment and typography-direction reviews are grounded. The
infrastructure adapter imports Phase 8 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["BrandInputPort"]


@runtime_checkable
class BrandInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
