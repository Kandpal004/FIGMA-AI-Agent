"""The Knowledge advisor port — grounding in design-orchestration best-practice (Phase 3).

Supplies curated principles as neutral :class:`RawSignal` s for a set of topics (page
composition, section ordering, above-the-fold priority, conversion sequencing, review gates,
progressive disclosure, …), so the ordering and sequencing decisions can be grounded in the
platform's canonical knowledge rather than convention. The infrastructure adapter imports Phase 3
and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
