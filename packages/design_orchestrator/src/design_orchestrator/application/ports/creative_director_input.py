"""The Phase 13 Creative Director port — grounds the review checkpoints and quality bar.

Supplies neutral :class:`RawSignal` s derived from the approved review (the quality gates and
anti-generic constraints). The infrastructure adapter imports that engine and translates; the
orchestrator domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["CreativeDirectorInputPort"]


@runtime_checkable
class CreativeDirectorInputPort(Protocol):
    """Gathers creative-director signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
