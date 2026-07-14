"""The Brand input port — the primary identity driver of the psychology model.

Supplies neutral :class:`RawSignal` s derived from the Phase-8 Brand Strategy report (its
guidelines bundle: archetype, emotions, tone, trust). The brand tells the psychology what
the customer should feel and trust; the infrastructure adapter imports Phase 8 and
translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from psychology.application.contracts import RawSignal
from psychology.domain.context.context import ProjectContext

__all__ = ["BrandInputPort"]


@runtime_checkable
class BrandInputPort(Protocol):
    """Gathers brand-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return brand-strategy signals for a project (may be empty)."""
        ...
