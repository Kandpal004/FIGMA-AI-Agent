"""The Phase 15 Component Intelligence port — grounds which components exist and where.

Supplies neutral :class:`RawSignal` s derived from the component composition (the included
components, their placement per page, and their compatibility). The infrastructure adapter
imports that engine and translates; the orchestrator domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["ComponentIntelligenceInputPort"]


@runtime_checkable
class ComponentIntelligenceInputPort(Protocol):
    """Gathers component-intelligence signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
