"""KnowledgeLinkAdapter — grounds research evidence in the Knowledge Engine (P3).

Implements the :class:`KnowledgeLinkPort` over the Phase-3 query service: it searches
the corpus for entries corresponding to a research claim and returns them as
:class:`KnowledgeLink` s. The research domain never imports Phase 3; this adapter is
the seam.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.reasoning.query import KnowledgeQuery

from research.application.ports.knowledge_link import KnowledgeLink
from research.domain.shared.value_objects import ResearchCategory

__all__ = ["KnowledgeLinkAdapter"]


class KnowledgeLinkAdapter:
    """Implements :class:`KnowledgeLinkPort` over the Phase-3 query service."""

    def __init__(self, query_service: KnowledgeQueryService) -> None:
        self._query = query_service

    async def link(
        self,
        claim: str,
        category: ResearchCategory,
        *,
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[KnowledgeLink]:
        viewer = tenant_id if isinstance(tenant_id, uuid.UUID) else None
        result = await self._query.search(
            claim, query=KnowledgeQuery(viewer_tenant_id=viewer, limit=limit or 3)
        )
        return [
            KnowledgeLink(
                knowledge_id=str(entry.knowledge_id),
                entry_version_id=str(entry.id),
                title=entry.title,
                statement=entry.statement,
                confidence=entry.confidence.score,
            )
            for entry in result.entries
        ]
