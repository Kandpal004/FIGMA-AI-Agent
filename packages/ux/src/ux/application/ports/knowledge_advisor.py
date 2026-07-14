"""The Knowledge advisor port — grounding in UX laws / heuristics / Baymard (Phase 3).

Supplies curated UX principles as neutral :class:`RawSignal` s for a set of UX topics, so
decisions can be grounded in the platform's canonical knowledge (Nielsen heuristics,
Baymard patterns, WCAG, the UX laws). The infrastructure adapter imports Phase 3 and
translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
