"""The Knowledge advisor port — grounding in Figma file-craft best-practice (Phase 3).

Supplies curated principles as neutral :class:`RawSignal` s for a set of topics (Figma file
organization, variable collections and modes, auto-layout, component sets and variants, published
styles, dev-mode handoff, responsive frames, …), so the file structure can be grounded in the
platform's canonical knowledge of how senior designers build files. The infrastructure adapter
imports Phase 3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
