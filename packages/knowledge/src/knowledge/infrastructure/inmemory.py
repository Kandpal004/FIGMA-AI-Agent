"""In-memory infrastructure adapters for the Knowledge Engine.

Real, dependency-free implementations of every port, backed by a dictionary.
They make the whole engine runnable and testable with no external services, and
they document each port's exact contract in the simplest possible form (the
database-backed adapters are checked against them). All query semantics are
delegated to the domain's :class:`KnowledgeQuery`, so behaviour is identical to
the SQL store.

Infrastructure only: the application and domain never import this module.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from knowledge.application.ports.clock import Clock
from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import RelationType
from knowledge.domain.entry.status import KnowledgeStatus
from knowledge.domain.reasoning.query import KnowledgeQuery
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.taxonomy.category import KnowledgeCategory

__all__ = [
    "InMemoryKnowledgeRepository",
    "InMemoryKnowledgeSearchPort",
    "InMemoryStorage",
    "InMemoryUnitOfWork",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class InMemoryStorage:
    """Process-lifetime storage shared by all in-memory units of work.

    Keyed by :class:`EntryVersionId`, so it naturally retains every version of
    every lineage — exactly what the immutable-versioning model requires.
    """

    def __init__(self) -> None:
        self.entries: dict[EntryVersionId, KnowledgeEntry] = {}


class InMemoryKnowledgeRepository:
    """Dict-backed :class:`KnowledgeRepository`."""

    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    async def save(self, entry: KnowledgeEntry) -> None:
        self._storage.entries[entry.id] = entry

    async def get(self, entry_version_id: EntryVersionId) -> KnowledgeEntry:
        entry = self._storage.entries.get(entry_version_id)
        if entry is None:
            raise NotFoundError(
                f"Knowledge entry version {entry_version_id} not found.",
                details={"entry_version_id": str(entry_version_id)},
            )
        return entry

    async def get_active(self, knowledge_id: KnowledgeId) -> KnowledgeEntry:
        versions = [
            e
            for e in self._storage.entries.values()
            if e.knowledge_id == knowledge_id and e.status is KnowledgeStatus.ACTIVE
        ]
        if not versions:
            raise NotFoundError(
                f"No active version for knowledge {knowledge_id}.",
                details={"knowledge_id": str(knowledge_id)},
            )
        return max(versions, key=lambda e: e.version)

    async def get_history(self, knowledge_id: KnowledgeId) -> Sequence[KnowledgeEntry]:
        versions = [
            e for e in self._storage.entries.values() if e.knowledge_id == knowledge_id
        ]
        return sorted(versions, key=lambda e: e.version)

    async def find(self, query: KnowledgeQuery) -> Sequence[KnowledgeEntry]:
        return [e for e in self._storage.entries.values() if query.matches(e)]

    async def get_many_active(
        self, knowledge_ids: Iterable[KnowledgeId]
    ) -> Sequence[KnowledgeEntry]:
        result: list[KnowledgeEntry] = []
        for knowledge_id in knowledge_ids:
            try:
                result.append(await self.get_active(knowledge_id))
            except NotFoundError:
                continue
        return result

    async def find_referencing(
        self,
        target: KnowledgeId,
        relation_types: frozenset[RelationType] | None = None,
    ) -> Sequence[KnowledgeEntry]:
        result: list[KnowledgeEntry] = []
        for entry in self._storage.entries.values():
            if entry.status is not KnowledgeStatus.ACTIVE:
                continue
            for relation in entry.relations:
                if relation.target == target and (
                    relation_types is None or relation.relation_type in relation_types
                ):
                    result.append(entry)
                    break
        return result


class InMemoryKnowledgeSearchPort:
    """A real structured keyword search over ACTIVE entries.

    Ranks candidate lineages by how many query terms appear in an entry's title,
    statement, description, or tags. This is the deterministic stand-in for the
    future Qdrant vector search; it satisfies the same port so it can be swapped
    without touching the application.
    """

    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    async def search(
        self,
        text: str,
        *,
        categories: Sequence[KnowledgeCategory] | None = None,
        limit: int | None = None,
    ) -> Sequence[KnowledgeId]:
        terms = {t for t in text.lower().split() if t}
        category_set = set(categories) if categories else None
        scored: list[tuple[int, int, KnowledgeId]] = []
        for entry in self._storage.entries.values():
            if entry.status is not KnowledgeStatus.ACTIVE:
                continue
            if category_set is not None and entry.category not in category_set:
                continue
            haystack = (
                f"{entry.title}\n{entry.statement}\n{entry.description}\n"
                + " ".join(t.value for t in entry.tags)
            ).lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, entry.version, entry.knowledge_id))
        scored.sort(reverse=True)
        ordered = [knowledge_id for _, _, knowledge_id in scored]
        return ordered[:limit] if limit is not None else ordered


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage (immediate writes)."""

    def __init__(self, storage: InMemoryStorage) -> None:
        self.entries = InMemoryKnowledgeRepository(storage)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def make_unit_of_work_factory(storage: InMemoryStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
