"""The Phase 14 Design Language port — grounds the visual language of the file.

Supplies neutral :class:`RawSignal` s derived from the Design Language spec (the Visual DNA,
typography voice). The infrastructure adapter imports that engine and translates; the figma-design
domain never imports it — nor any Figma SDK.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext

__all__ = ["DesignLanguageInputPort"]


@runtime_checkable
class DesignLanguageInputPort(Protocol):
    """Gathers design-language signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
