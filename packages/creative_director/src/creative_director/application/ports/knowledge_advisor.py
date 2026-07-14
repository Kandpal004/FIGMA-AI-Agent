"""The Knowledge advisor port — grounding in premium-ecommerce review standards (Phase 3).

Supplies curated review principles as neutral :class:`RawSignal` s for a set of topics
(premium ecommerce standards, CRO, trust, typography, spacing, accessibility, platform
feasibility, …), so the Creative Director's rulings can be grounded in the platform's
canonical knowledge rather than opinion. The infrastructure adapter imports Phase 3 and
translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
