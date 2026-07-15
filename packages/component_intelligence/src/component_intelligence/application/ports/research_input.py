"""The Phase 6 Research — grounds decisions in primary findings.

Supplies neutral RawSignals derived from its upstream engine. The infrastructure adapter
imports that engine and translates; the component-intelligence domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext

__all__ = ["ResearchInputPort"]


@runtime_checkable
class ResearchInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
