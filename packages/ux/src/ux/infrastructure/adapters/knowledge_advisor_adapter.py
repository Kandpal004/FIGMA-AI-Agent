"""KnowledgeAdvisorAdapter — grounds the UX strategy in the Phase-3 Knowledge Engine.

Implements :class:`KnowledgeAdvisorPort` over the Phase-3 query service: for each UX topic
it searches the curated corpus and returns the matching principles as neutral
:class:`RawSignal` s (provenance ``KNOWLEDGE``), de-duplicated by lineage. The UX domain
never imports Phase 3; this adapter is the seam.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.reasoning.query import KnowledgeQuery

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext
from ux.domain.shared.value_objects import ProvenanceKind

__all__ = ["KnowledgeAdvisorAdapter"]

_PER_TOPIC = 2


class KnowledgeAdvisorAdapter:
    """Implements :class:`KnowledgeAdvisorPort` over the Phase-3 query service."""

    def __init__(self, query_service: KnowledgeQueryService) -> None:
        self._query = query_service

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        viewer = self._tenant(project)
        seen: set[str] = set()
        signals: list[RawSignal] = []
        for topic in topics:
            result = await self._query.search(
                topic, query=KnowledgeQuery(viewer_tenant_id=viewer, limit=_PER_TOPIC)
            )
            for entry in result.entries:
                key = str(entry.knowledge_id)
                if key in seen:
                    continue
                seen.add(key)
                signals.append(
                    RawSignal(
                        provenance=ProvenanceKind.KNOWLEDGE, external_ref=key,
                        claim=entry.statement, confidence=entry.confidence.score,
                        statement=entry.title, source_name="Knowledge Engine",
                        tags=(entry.category.value,),
                    )
                )
        return signals

    @staticmethod
    def _tenant(project: ProjectContext) -> uuid.UUID | None:
        if not project.tenant_id:
            return None
        try:
            return uuid.UUID(project.tenant_id)
        except ValueError:
            return None
