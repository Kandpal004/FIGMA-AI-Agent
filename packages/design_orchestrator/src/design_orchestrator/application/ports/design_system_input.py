"""The Phase 16 Design System port — grounds tokens, variants, themes, and constraints.

Supplies neutral :class:`RawSignal` s derived from the Design System spec (the token set,
component specs with their variants and platform mappings, themes, and constraints). The
infrastructure adapter imports that engine and translates; the orchestrator domain never imports
it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["DesignSystemInputPort"]


@runtime_checkable
class DesignSystemInputPort(Protocol):
    """Gathers design-system signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
