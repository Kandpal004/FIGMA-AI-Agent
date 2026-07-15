"""The Phase 15 Component Intelligence port — grounds which component sets to build.

Supplies neutral :class:`RawSignal` s derived from the component composition (the included
components and their variants). The infrastructure adapter imports that engine and translates; the
figma-design domain never imports it — nor any Figma SDK.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext

__all__ = ["ComponentIntelligenceInputPort"]


@runtime_checkable
class ComponentIntelligenceInputPort(Protocol):
    """Gathers component-intelligence signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
