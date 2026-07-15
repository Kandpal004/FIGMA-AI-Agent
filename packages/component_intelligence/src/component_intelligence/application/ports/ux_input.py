"""The Phase 10 UX Strategy — grounds user purpose and interaction.

Supplies neutral RawSignals derived from its upstream engine. The infrastructure adapter
imports that engine and translates; the component-intelligence domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext

__all__ = ["UXInputPort"]


@runtime_checkable
class UXInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
