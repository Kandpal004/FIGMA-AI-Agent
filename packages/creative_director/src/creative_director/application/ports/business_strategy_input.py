"""The Business-Strategy input port (Phase 7).

Supplies neutral :class:`RawSignal` s derived from the business strategy — positioning and
commercial goals — so business-alignment reviews are grounded. The infrastructure adapter
imports Phase 7 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["BusinessStrategyInputPort"]


@runtime_checkable
class BusinessStrategyInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
