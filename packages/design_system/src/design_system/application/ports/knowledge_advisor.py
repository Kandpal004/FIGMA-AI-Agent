"""The Knowledge advisor port — grounding in design-system best-practice (Phase 3).

Supplies curated design-system principles as neutral :class:`RawSignal` s for a set of topics
(design tokens, three-tier token architecture, theming, dark mode, accessibility/WCAG, RTL,
component variants and states, atomic design, Shopify/Polaris and Magento patterns,
anti-patterns, …), so the token architecture and component specs can be grounded in the
platform's canonical knowledge rather than convention. The infrastructure adapter imports Phase
3 and translates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["KnowledgeAdvisorPort"]


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Advises with curated knowledge principles as neutral signals."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        """Return knowledge principles relevant to the given topics (may be empty)."""
        ...
