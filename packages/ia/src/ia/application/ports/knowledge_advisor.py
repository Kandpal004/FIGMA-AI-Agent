"""The Knowledge advisor port — grounding in IA / navigation / SEO best-practice (Phase 3).

Supplies curated IA principles as neutral :class:`RawSignal` s for a set of IA topics, so
structural decisions can be grounded in the platform's canonical knowledge. The
infrastructure adapter imports Phase 3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
