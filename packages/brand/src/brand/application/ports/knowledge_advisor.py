"""The Knowledge advisor port — grounding brand principles in Phase-3 Knowledge.

Supplies curated brand/design principles as neutral :class:`RawSignal` s for a set of
brand topics, so identity and creative direction can be grounded in the platform's
canonical knowledge. The infrastructure adapter imports Phase 3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from brand.application.contracts import RawSignal
from brand.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
