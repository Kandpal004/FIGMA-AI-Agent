"""The Knowledge advisor port — grounding in the Phase-3 Knowledge Engine.

Supplies curated best-practice principles as neutral :class:`RawInsight` s for a set of
strategic topics, so decisions can be grounded in the platform's canonical knowledge.
The infrastructure adapter imports Phase 3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from strategy.application.contracts import RawInsight
from strategy.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral insights."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawInsight]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
