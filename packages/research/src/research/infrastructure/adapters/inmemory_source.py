"""InMemorySource — a manual/in-memory source adapter.

Returns pre-supplied raw artifacts for the sources it is configured with. It is the
honest default for local running and tests (a stand-in for the future Firecrawl /
Playwright / MCP adapters), and it demonstrates the :class:`ResearchSourcePort`
contract in the simplest possible form.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from research.domain.collection.artifact import RawArtifact
from research.domain.shared.ids import ResearchSourceId
from research.domain.source.source import ResearchSource

__all__ = ["InMemorySource"]


class InMemorySource:
    """A source adapter returning fixed artifacts per source id."""

    def __init__(
        self, artifacts: Mapping[ResearchSourceId, Sequence[RawArtifact]] | None = None
    ) -> None:
        self._artifacts: dict[ResearchSourceId, tuple[RawArtifact, ...]] = {
            sid: tuple(items) for sid, items in (artifacts or {}).items()
        }

    def register(
        self, source_id: ResearchSourceId, artifacts: Sequence[RawArtifact]
    ) -> None:
        """Register the artifacts a source will return."""
        self._artifacts[source_id] = tuple(artifacts)

    async def collect(self, source: ResearchSource) -> Sequence[RawArtifact]:
        return self._artifacts.get(source.id, ())
