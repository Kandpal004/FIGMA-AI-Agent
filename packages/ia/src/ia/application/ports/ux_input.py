"""The UX input port — the primary driver of the information architecture.

Supplies neutral :class:`RawSignal` s derived from the Phase-10 UX Strategy report (its
design brief bundle: page blueprints, CTAs, priorities, navigation, friction). This is the
IA's principal input: the structure is built to serve the UX strategy. The infrastructure
adapter imports Phase 10 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext

__all__ = ["UXInputPort"]


@runtime_checkable
class UXInputPort(Protocol):
    """Gathers UX-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return UX-strategy signals for a project (may be empty)."""
        ...
