"""The Phase 17 Design Orchestrator port — the primary driver of the Figma model.

Supplies neutral :class:`RawSignal` s derived from the design-execution plan (the ordered pages
and sections, the token/variant bindings, the responsive directives). The infrastructure adapter
imports that engine and translates; the figma-design domain never imports it — nor any Figma SDK.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext

__all__ = ["DesignOrchestratorInputPort"]


@runtime_checkable
class DesignOrchestratorInputPort(Protocol):
    """Gathers design-orchestrator signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
