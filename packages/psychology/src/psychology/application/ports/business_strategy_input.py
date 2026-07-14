"""The Business Strategy input port — the commercial driver of the psychology model.

Supplies neutral :class:`RawSignal` s derived from the Phase-7 Business Strategy report
(its directive bundle: positioning, emotions, required trust, prioritized decisions). The
infrastructure adapter imports Phase 7 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from psychology.application.contracts import RawSignal
from psychology.domain.context.context import ProjectContext

__all__ = ["BusinessStrategyInputPort"]


@runtime_checkable
class BusinessStrategyInputPort(Protocol):
    """Gathers business-strategy signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return business-strategy signals for a project (may be empty)."""
        ...
