"""The Research input port — evidence from the Phase-6 Research Engine.

Supplies neutral :class:`RawInsight` s derived from a project's research report
(entities and provenance-tracked evidence). The infrastructure adapter imports Phase 6
and translates; the domain and application never do.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from strategy.application.contracts import RawInsight
from strategy.domain.context.context import ProjectContext

__all__ = ["ResearchInputPort"]


@runtime_checkable
class ResearchInputPort(Protocol):
    """Gathers research evidence as neutral insights."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        """Return research-derived insights for a project (may be empty)."""
        ...
