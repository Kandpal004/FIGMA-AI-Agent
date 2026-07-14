"""The Psychology input port — trust/objection placement signals from Phase 9.

Supplies neutral :class:`RawSignal` s from the Phase-9 psychology model (trust moments,
objections, decision triggers) so section placement and trust structure are grounded in how
the customer decides. The infrastructure adapter imports Phase 9 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext

__all__ = ["PsychologyInputPort"]


@runtime_checkable
class PsychologyInputPort(Protocol):
    """Gathers psychology signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return psychology signals for a project (may be empty)."""
        ...
