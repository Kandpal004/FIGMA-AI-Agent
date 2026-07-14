"""KnowledgeEngineSource — treats the Knowledge Engine (P3) as a research source.

Implements :class:`ResearchSourcePort` by collecting the Knowledge Engine's active
entries into a single structured artifact (evidence + entities), which the
StructuredExtractor then turns into candidates. This lets curated knowledge flow into
a research report alongside external sources. The research domain never imports Phase
3; this adapter is the seam.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.reasoning.query import KnowledgeQuery

from research.domain.collection.artifact import RawArtifact
from research.domain.shared.ids import ArtifactId
from research.domain.shared.value_objects import ArtifactKind
from research.domain.source.source import ResearchSource

__all__ = ["KnowledgeEngineSource"]

_MAX_ENTRIES = 50


class KnowledgeEngineSource:
    """Collects active Knowledge-Engine entries as a structured artifact."""

    def __init__(self, query_service: KnowledgeQueryService) -> None:
        self._query = query_service

    async def collect(self, source: ResearchSource) -> Sequence[RawArtifact]:
        result = await self._query.find(KnowledgeQuery(limit=_MAX_ENTRIES))
        payload = json.dumps(
            {
                "evidence": [
                    {
                        "claim": entry.statement,
                        "confidence": entry.confidence.score,
                        "category": "knowledge",
                        "snippet": entry.title,
                    }
                    for entry in result.entries
                ],
                "entities": [
                    {
                        "type": "design_pattern",
                        "label": entry.title,
                        "confidence": entry.confidence.score,
                    }
                    for entry in result.entries
                ],
            }
        )
        return [
            RawArtifact(
                id=ArtifactId.new(),
                source_id=source.id,
                kind=ArtifactKind.STRUCTURED,
                payload=payload,
                locator=source.locator,
                collected_at=datetime.now(UTC),
                metadata={"entries": str(len(result.entries))},
            )
        ]
