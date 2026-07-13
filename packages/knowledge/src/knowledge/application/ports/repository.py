"""The knowledge repository port — the persistence interface the app depends on.

Expresses *what* the application needs from storage without saying *how*. The
infrastructure layer supplies concrete implementations (in-memory, SQLAlchemy);
neither the application nor the domain imports a database driver.

The read model is shaped by the versioning strategy: entries are addressed either
by their exact version (:meth:`get`) or by lineage (:meth:`get_active`,
:meth:`get_history`). ``save`` is an upsert on the version id — it persists a new
version *and* records a lifecycle status change on an existing one. Structured
retrieval is :meth:`find`, which returns every entry satisfying a query's
:meth:`~knowledge.domain.reasoning.query.KnowledgeQuery.matches` predicate
(ranking and limiting are the query service's job, applied uniformly).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol, runtime_checkable

from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import RelationType
from knowledge.domain.reasoning.query import KnowledgeQuery
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId

__all__ = ["KnowledgeRepository"]


@runtime_checkable
class KnowledgeRepository(Protocol):
    """Loads and persists :class:`KnowledgeEntry` versions."""

    async def save(self, entry: KnowledgeEntry) -> None:
        """Insert a new version, or update an existing one (by version id)."""
        ...

    async def get(self, entry_version_id: EntryVersionId) -> KnowledgeEntry:
        """Return one exact version.

        Raises:
            NotFoundError: If no such version exists.
        """
        ...

    async def get_active(self, knowledge_id: KnowledgeId) -> KnowledgeEntry:
        """Return the current ACTIVE version of a lineage.

        Raises:
            NotFoundError: If the lineage has no ACTIVE version.
        """
        ...

    async def get_history(self, knowledge_id: KnowledgeId) -> Sequence[KnowledgeEntry]:
        """Return every version of a lineage, ordered by ascending version."""
        ...

    async def find(self, query: KnowledgeQuery) -> Sequence[KnowledgeEntry]:
        """Return every entry matching ``query`` (unranked, unlimited)."""
        ...

    async def get_many_active(
        self, knowledge_ids: Iterable[KnowledgeId]
    ) -> Sequence[KnowledgeEntry]:
        """Return the ACTIVE versions for the given lineages.

        Lineages with no ACTIVE version are silently omitted — used to resolve
        relationship targets, some of which may be draft or archived.
        """
        ...

    async def find_referencing(
        self,
        target: KnowledgeId,
        relation_types: frozenset[RelationType] | None = None,
    ) -> Sequence[KnowledgeEntry]:
        """Return ACTIVE entries with an edge pointing *at* ``target``.

        Enables reverse graph traversal — e.g. "which principles SUPPORT this
        one?" — which forward-only relations cannot answer. Restricted to the
        given relation types when provided.
        """
        ...
