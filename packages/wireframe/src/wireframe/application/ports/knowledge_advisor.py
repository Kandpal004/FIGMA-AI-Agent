"""The Knowledge advisor port — grounding in wireframe/planning best-practice (Phase 3).

Supplies curated planning principles as neutral :class:`RawSignal` s for a set of topics
(section ordering, component composition, approval gating, accessibility, performance
budgets, …), so structural decisions can be grounded in the platform's canonical knowledge.
The infrastructure adapter imports Phase 3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from wireframe.application.contracts import RawSignal
from wireframe.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
