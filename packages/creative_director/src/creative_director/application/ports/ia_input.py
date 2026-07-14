"""The Information Architecture input port (Phase 11).

Supplies neutral :class:`RawSignal` s derived from the IA report — pages, section structure,
navigation, hierarchy — so information-hierarchy and structure reviews are grounded. The
infrastructure adapter imports Phase 11 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["IAInputPort"]


@runtime_checkable
class IAInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
