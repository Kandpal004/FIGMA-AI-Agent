"""KnowledgeQueryService — structured retrieval and graph traversal.

The read side of the engine. It applies a query's deterministic filter and
ranking, resolves an entry's relationship neighbourhood, and (when a semantic
search port is wired) uses it purely for candidate generation before falling back
to authoritative structured ranking. It performs no writes and holds no state; the
repository and optional search port are injected.

Ranking lives here (not in the repositories) so every backend orders results
identically: the repository returns the matching set, and this service sorts by
the query's :meth:`~knowledge.domain.reasoning.query.KnowledgeQuery.sort_key` and
applies the limit.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from knowledge.application.ports.repository import KnowledgeRepository
from knowledge.application.ports.search_port import KnowledgeSearchPort
from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import CONFLICTING_RELATIONS, SUPPORTING_RELATIONS
from knowledge.domain.reasoning.query import KnowledgeQuery, QueryResult, SortOrder
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId

__all__ = ["KnowledgeQueryService", "Neighborhood"]


@dataclass(frozen=True, slots=True)
class Neighborhood:
    """An entry together with its directly related ACTIVE entries."""

    entry: KnowledgeEntry
    supporting: tuple[KnowledgeEntry, ...]
    contradicting: tuple[KnowledgeEntry, ...]


class KnowledgeQueryService:
    """Deterministic structured retrieval over the corpus."""

    def __init__(
        self,
        repository: KnowledgeRepository,
        search: KnowledgeSearchPort | None = None,
    ) -> None:
        self._repo = repository
        self._search = search

    async def find(self, query: KnowledgeQuery) -> QueryResult:
        """Return the ranked, limited result set for a structured query."""
        matched = list(await self._repo.find(query))
        matched.sort(key=query.sort_key, reverse=True)
        total = len(matched)
        entries = matched[: query.limit] if query.limit is not None else matched
        return QueryResult(entries=tuple(entries), total=total)

    async def get(self, entry_version_id: EntryVersionId) -> KnowledgeEntry:
        """Return one exact version (raises ``NotFoundError`` if absent)."""
        return await self._repo.get(entry_version_id)

    async def get_active(self, knowledge_id: KnowledgeId) -> KnowledgeEntry:
        """Return the current ACTIVE version of a lineage."""
        return await self._repo.get_active(knowledge_id)

    async def history(self, knowledge_id: KnowledgeId) -> Sequence[KnowledgeEntry]:
        """Return every version of a lineage, oldest first."""
        return await self._repo.get_history(knowledge_id)

    async def neighborhood(self, knowledge_id: KnowledgeId) -> Neighborhood:
        """Resolve an entry's supporting and contradicting ACTIVE neighbours."""
        entry = await self._repo.get_active(knowledge_id)
        supporting_targets = [
            r.target for r in entry.relations if r.relation_type in SUPPORTING_RELATIONS
        ]
        contradicting_targets = [
            r.target for r in entry.relations if r.relation_type in CONFLICTING_RELATIONS
        ]
        supporting = await self._repo.get_many_active(supporting_targets)
        contradicting = await self._repo.get_many_active(contradicting_targets)
        return Neighborhood(
            entry=entry,
            supporting=tuple(supporting),
            contradicting=tuple(contradicting),
        )

    async def search(
        self,
        text: str,
        *,
        query: KnowledgeQuery | None = None,
    ) -> QueryResult:
        """Free-text search: semantic candidate generation when available, else a
        structured text query — always finished with authoritative structured
        ranking.
        """
        base = query or KnowledgeQuery(sort=SortOrder.RELEVANCE)
        if self._search is None:
            return await self.find(
                KnowledgeQuery(
                    categories=base.categories,
                    statuses=base.statuses,
                    viewer_tenant_id=base.viewer_tenant_id,
                    text=text,
                    sort=base.sort,
                    limit=base.limit,
                )
            )
        candidate_ids = await self._search.search(
            text, categories=tuple(base.categories) or None, limit=base.limit
        )
        candidates = await self._repo.get_many_active(candidate_ids)
        ranked = [e for e in candidates if base.matches(e)]
        ranked.sort(key=base.sort_key, reverse=True)
        entries = ranked[: base.limit] if base.limit is not None else ranked
        return QueryResult(entries=tuple(entries), total=len(ranked))
