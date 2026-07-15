"""The Phase 13 Creative Director port — grounds the aesthetic constraints.

Supplies neutral :class:`RawSignal` s derived from the creative review (approved direction,
anti-generic constraints, distinctiveness signals). The infrastructure adapter imports that
engine and translates; the design-system domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["CreativeDirectorInputPort"]


@runtime_checkable
class CreativeDirectorInputPort(Protocol):
    """Gathers creative-director signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
