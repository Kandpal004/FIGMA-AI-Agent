"""ProjectMemorySource — treats Phase-2 Project Memory as a research source.

Implements :class:`ResearchSourcePort` by collecting a project's memory records
(business goals, brand tokens, prior findings) into a structured artifact. The
source's locator ``uri`` carries the project id. The research domain never imports
Phase 2; this adapter is the seam.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from director.application.memory.memory_engine import MemoryEngine
from director.domain.shared.ids import ProjectId

from research.domain.collection.artifact import RawArtifact
from research.domain.shared.ids import ArtifactId
from research.domain.shared.value_objects import ArtifactKind
from research.domain.source.source import ResearchSource

__all__ = ["ProjectMemorySource"]


class ProjectMemorySource:
    """Collects a project's Phase-2 memory records as a structured artifact."""

    def __init__(self, memory: MemoryEngine) -> None:
        self._memory = memory

    async def collect(self, source: ResearchSource) -> Sequence[RawArtifact]:
        project_id = ProjectId.from_string(source.locator.uri)
        context = await self._memory.load_context(project_id)
        payload = json.dumps(
            {
                "evidence": [
                    {
                        "claim": record.body,
                        "confidence": record.confidence,
                        "category": "memory",
                        "snippet": record.title,
                    }
                    for record in context.records
                ]
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
                metadata={"records": str(len(context.records))},
            )
        ]
