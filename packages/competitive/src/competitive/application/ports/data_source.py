"""The Competitor Data-Source port — the engine's only door to competitor data.

The engine never scrapes, drives a browser, or calls an LLM. It asks this port for
structured :class:`ObservationSet` about the brief's competitors, and works with
whatever the adapter delivers. Manual/in-memory today; Firecrawl, Playwright,
Browser/Figma MCP, Context7, and OpenRouter are future adapters behind this same
interface — the domain is blind to their origin.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from competitive.domain.competitor.observation import ObservationSet
from competitive.domain.report.brief import CompetitiveBrief

__all__ = ["CompetitorDataSourcePort"]


@runtime_checkable
class CompetitorDataSourcePort(Protocol):
    """Supplies structured observations about the competitors in a brief."""

    async def gather(self, brief: CompetitiveBrief) -> ObservationSet:
        """Return the structured observations available for the brief's
        competitors. May be empty (the engine then produces a minimal report)."""
        ...
