"""The Phase 14 Design Language port — grounds the visual language and typography choices.

Supplies neutral :class:`RawSignal` s derived from the Design Language spec (the Visual DNA and
abstract token intent). The infrastructure adapter imports that engine and translates; the
orchestrator domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["DesignLanguageInputPort"]


@runtime_checkable
class DesignLanguageInputPort(Protocol):
    """Gathers design-language signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
