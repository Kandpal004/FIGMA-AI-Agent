"""The Brand input port — optional brand structure signals from Phase 8.

Supplies neutral :class:`RawSignal` s from the Phase-8 brand model. Optional: a null adapter
is valid when no brand strategy is available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext

__all__ = ["BrandInputPort"]


@runtime_checkable
class BrandInputPort(Protocol):
    """Gathers brand-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return brand-strategy signals for a project (may be empty)."""
        ...
