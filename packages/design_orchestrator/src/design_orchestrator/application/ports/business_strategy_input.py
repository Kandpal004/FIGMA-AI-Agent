"""The Phase 7 Business Strategy port — grounds priority and the performance directive.

Supplies neutral :class:`RawSignal` s derived from the business strategy (positioning, conversion
priorities). The infrastructure adapter imports that engine and translates; the orchestrator
domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["BusinessStrategyInputPort"]


@runtime_checkable
class BusinessStrategyInputPort(Protocol):
    """Gathers business-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
