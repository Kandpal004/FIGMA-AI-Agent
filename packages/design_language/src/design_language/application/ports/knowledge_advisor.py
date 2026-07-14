"""The Knowledge advisor port — grounding in premium visual-system best-practice (Phase 3).

Supplies curated design principles as neutral :class:`RawSignal` s for a set of topics
(premium visual systems, typographic scales, spacing rhythm, restraint, timelessness, industry
conventions, …), so the visual language is grounded in the platform's canonical knowledge
rather than taste. The infrastructure adapter imports Phase 3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_language.application.contracts import RawSignal
from design_language.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
