"""The Brand input port — brand tone and trust into the UX strategy.

Supplies neutral :class:`RawSignal` s derived from the Phase-8 Brand Strategy report (its
guidelines bundle: tone, trust, personality). The infrastructure adapter imports Phase 8
and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext

__all__ = ["BrandInputPort"]


@runtime_checkable
class BrandInputPort(Protocol):
    """Gathers brand-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return brand-strategy signals for a project (may be empty)."""
        ...
