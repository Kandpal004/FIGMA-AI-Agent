"""The Customer-Psychology input port (Phase 9).

Supplies neutral :class:`RawSignal` s derived from the customer psychology — journey stages,
objections, trust needs — so psychology-alignment and trust reviews are grounded. The
infrastructure adapter imports Phase 9 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["PsychologyInputPort"]


@runtime_checkable
class PsychologyInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
