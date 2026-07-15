"""The Phase 16 Design System port — grounds the variables, styles, and component sets.

Supplies neutral :class:`RawSignal` s derived from the Design System spec (the token set, themes,
component specs). The infrastructure adapter imports that engine and translates; the figma-design
domain never imports it — nor any Figma SDK.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext

__all__ = ["DesignSystemInputPort"]


@runtime_checkable
class DesignSystemInputPort(Protocol):
    """Gathers design-system signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
