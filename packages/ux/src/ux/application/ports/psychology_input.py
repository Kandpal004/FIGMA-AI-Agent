"""The Psychology input port — the primary driver of the UX strategy.

Supplies neutral :class:`RawSignal` s derived from the Phase-9 Customer Psychology report
(its UX directive bundle: awareness, journey stages with friction/trust/emotion,
objections, decision triggers, feasible behaviors). This is the UX strategy's principal
input: the experience is architected around how the customer decides. The infrastructure
adapter imports Phase 9 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext

__all__ = ["PsychologyInputPort"]


@runtime_checkable
class PsychologyInputPort(Protocol):
    """Gathers customer-psychology signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return psychology signals for a project (may be empty)."""
        ...
