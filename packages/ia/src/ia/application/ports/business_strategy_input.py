"""The Business Strategy input port — commercial goals into the IA from Phase 7.

Supplies neutral :class:`RawSignal` s from the Phase-7 business strategy (goals,
positioning). Optional: a null adapter is valid when no business strategy is available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext

__all__ = ["BusinessStrategyInputPort"]


@runtime_checkable
class BusinessStrategyInputPort(Protocol):
    """Gathers business-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return business-strategy signals for a project (may be empty)."""
        ...
