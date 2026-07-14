"""Collector — stage 1: gather raw artifacts from the request's sources.

For each enabled source it resolves the source's adapter (via a resolver from the
registry) and collects the source into raw artifacts. It fetches nothing itself —
all acquisition is behind the :class:`ResearchSourcePort`. Pure orchestration.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from research.application.ports.source_port import ResearchSourcePort
from research.domain.collection.artifact import RawArtifact
from research.domain.source.source import ResearchSource

__all__ = ["Collector"]


class Collector:
    """Collects raw artifacts from a set of sources."""

    async def collect(
        self,
        sources: Sequence[ResearchSource],
        resolve_source: Callable[[ResearchSource], ResearchSourcePort],
    ) -> tuple[RawArtifact, ...]:
        artifacts: list[RawArtifact] = []
        for source in sources:
            port = resolve_source(source)
            artifacts.extend(await port.collect(source))
        return tuple(artifacts)
