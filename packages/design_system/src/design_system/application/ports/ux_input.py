"""The Phase 10 UX Strategy port — grounds interaction, accessibility, and state tokens.

Supplies neutral :class:`RawSignal` s derived from the UX strategy (interaction patterns, a11y
targets, responsive priorities). The infrastructure adapter imports that engine and translates;
the design-system domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["UXInputPort"]


@runtime_checkable
class UXInputPort(Protocol):
    """Gathers UX-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
