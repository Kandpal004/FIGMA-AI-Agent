"""The Source port — the engine's door to raw data collection.

The engine never fetches; it asks a :class:`ResearchSourcePort` adapter to *collect*
a source into raw artifacts. Manual/in-memory today; Firecrawl, Playwright/Browser
MCP, Figma MCP, Context7, and search providers are future adapters behind this same
interface. The domain is blind to which provider fulfilled a source.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from research.domain.collection.artifact import RawArtifact
from research.domain.source.source import ResearchSource

__all__ = ["ResearchSourcePort"]


@runtime_checkable
class ResearchSourcePort(Protocol):
    """Collects a source into raw artifacts."""

    async def collect(self, source: ResearchSource) -> Sequence[RawArtifact]:
        """Return the raw artifacts collected from ``source`` (may be empty)."""
        ...
