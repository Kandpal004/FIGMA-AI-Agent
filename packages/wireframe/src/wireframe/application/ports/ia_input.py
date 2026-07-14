"""The Information Architecture input port — the primary driver of the wireframe plan.

Supplies neutral :class:`RawSignal` s derived from the Phase-11 IA report (its wireframe
brief bundle: pages, sections, priorities, navigation, relationships, discovery). This is the
plan's principal input: the wireframe structure is built to execute the information
architecture. The infrastructure adapter imports Phase 11 and translates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from wireframe.application.contracts import RawSignal
from wireframe.domain.context.context import ProjectContext

__all__ = ["IAInputPort"]


@runtime_checkable
class IAInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
