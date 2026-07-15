"""The Phase 8 Brand Strategy port — grounds colour, type, and voice tokens.

Supplies neutral :class:`RawSignal` s derived from the brand strategy (palette, typography voice,
personality). The infrastructure adapter imports that engine and translates; the design-system
domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["BrandInputPort"]


@runtime_checkable
class BrandInputPort(Protocol):
    """Gathers brand-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
