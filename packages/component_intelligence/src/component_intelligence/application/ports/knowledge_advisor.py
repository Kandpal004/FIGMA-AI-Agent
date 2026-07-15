"""The Knowledge advisor port — grounding in ecommerce component best-practice (Phase 3).

Supplies curated component principles as neutral :class:`RawSignal` s for a set of topics
(ecommerce component patterns, CRO components, trust components, atomic design, component
composition, anti-patterns, …), so component decisions can be grounded in the platform's
canonical knowledge rather than convention. The infrastructure adapter imports Phase 3 and
translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
