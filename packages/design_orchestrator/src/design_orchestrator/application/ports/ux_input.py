"""The Phase 10 UX Strategy port — grounds interaction and accessibility directives.

Supplies neutral :class:`RawSignal` s derived from the UX strategy (interaction patterns and
accessibility targets). The infrastructure adapter imports that engine and translates; the
orchestrator domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["UXInputPort"]


@runtime_checkable
class UXInputPort(Protocol):
    """Gathers UX-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
