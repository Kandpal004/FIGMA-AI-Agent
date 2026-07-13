"""SQLAlchemy implementation of the knowledge repository.

Operates on an injected :class:`AsyncSession` and translates at the boundary via
the mappers, so no ORM object escapes into the application. To guarantee semantics
identical to the in-memory store, structured retrieval fetches a candidate set via
SQL (narrowed by the cheap, indexed facets — status, category, scope) and then
applies the domain query's full ``matches`` predicate in Python. For a curated
corpus this is both correct and fast.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.errors import NotFoundError

from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import RelationType
from knowledge.domain.entry.status import KnowledgeStatus
from knowledge.domain.reasoning.query import KnowledgeQuery
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.infrastructure.persistence import mappers
from knowledge.infrastructure.persistence.models import KnowledgeEntryModel

__all__ = ["SqlAlchemyKnowledgeRepository", "SqlAlchemySessionScopedRepository"]


class SqlAlchemyKnowledgeRepository:
    """Postgres-backed :class:`KnowledgeRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, entry: KnowledgeEntry) -> None:
        model = await self._session.get(KnowledgeEntryModel, entry.id.value)
        if model is None:
            self._session.add(mappers.entry_to_model(entry))
        else:
            mappers.apply_entry(model, entry)

    async def get(self, entry_version_id: EntryVersionId) -> KnowledgeEntry:
        model = await self._session.get(KnowledgeEntryModel, entry_version_id.value)
        if model is None:
            raise NotFoundError(
                f"Knowledge entry version {entry_version_id} not found.",
                details={"entry_version_id": str(entry_version_id)},
            )
        return mappers.model_to_entry(model)

    async def get_active(self, knowledge_id: KnowledgeId) -> KnowledgeEntry:
        stmt = (
            select(KnowledgeEntryModel)
            .where(
                KnowledgeEntryModel.knowledge_id == knowledge_id.value,
                KnowledgeEntryModel.status == KnowledgeStatus.ACTIVE.value,
            )
            .order_by(KnowledgeEntryModel.version.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalars().first()
        if model is None:
            raise NotFoundError(
                f"No active version for knowledge {knowledge_id}.",
                details={"knowledge_id": str(knowledge_id)},
            )
        return mappers.model_to_entry(model)

    async def get_history(self, knowledge_id: KnowledgeId) -> Sequence[KnowledgeEntry]:
        stmt = (
            select(KnowledgeEntryModel)
            .where(KnowledgeEntryModel.knowledge_id == knowledge_id.value)
            .order_by(KnowledgeEntryModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [mappers.model_to_entry(m) for m in rows]

    async def find(self, query: KnowledgeQuery) -> Sequence[KnowledgeEntry]:
        stmt = select(KnowledgeEntryModel)
        if query.statuses:
            stmt = stmt.where(
                KnowledgeEntryModel.status.in_([s.value for s in query.statuses])
            )
        if query.categories:
            stmt = stmt.where(
                KnowledgeEntryModel.category.in_([c.value for c in query.categories])
            )
        rows = (await self._session.execute(stmt)).scalars().all()
        entries = (mappers.model_to_entry(m) for m in rows)
        # Apply the full, authoritative predicate in the domain.
        return [e for e in entries if query.matches(e)]

    async def get_many_active(
        self, knowledge_ids: Iterable[KnowledgeId]
    ) -> Sequence[KnowledgeEntry]:
        ids = {k.value for k in knowledge_ids}
        if not ids:
            return []
        stmt = select(KnowledgeEntryModel).where(
            KnowledgeEntryModel.knowledge_id.in_(ids),
            KnowledgeEntryModel.status == KnowledgeStatus.ACTIVE.value,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        # Highest active version per lineage.
        best: dict[object, KnowledgeEntryModel] = {}
        for model in rows:
            current = best.get(model.knowledge_id)
            if current is None or model.version > current.version:
                best[model.knowledge_id] = model
        return [mappers.model_to_entry(m) for m in best.values()]

    async def find_referencing(
        self,
        target: KnowledgeId,
        relation_types: frozenset[RelationType] | None = None,
    ) -> Sequence[KnowledgeEntry]:
        stmt = select(KnowledgeEntryModel).where(
            KnowledgeEntryModel.status == KnowledgeStatus.ACTIVE.value
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        target_str = str(target)
        wanted = {rt.value for rt in relation_types} if relation_types else None
        result: list[KnowledgeEntry] = []
        for model in rows:
            for relation in model.relations:
                if relation.get("target") == target_str and (
                    wanted is None or relation.get("relation_type") in wanted
                ):
                    result.append(mappers.model_to_entry(model))
                    break
        return result


class SqlAlchemySessionScopedRepository:
    """A read-side :class:`KnowledgeRepository` that opens a fresh session per call.

    The transactional :class:`SqlAlchemyKnowledgeRepository` is bound to one
    session and belongs inside a unit of work. Reads (the query service and
    reasoner) run outside any transaction and must not share a long-lived session,
    so this variant scopes a short session to each read and delegates to the
    session-bound repository. It exposes only read operations.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, entry: KnowledgeEntry) -> None:  # pragma: no cover - reads only
        raise NotImplementedError("Use a unit of work for writes.")

    async def get(self, entry_version_id: EntryVersionId) -> KnowledgeEntry:
        async with self._session_factory() as session:
            return await SqlAlchemyKnowledgeRepository(session).get(entry_version_id)

    async def get_active(self, knowledge_id: KnowledgeId) -> KnowledgeEntry:
        async with self._session_factory() as session:
            return await SqlAlchemyKnowledgeRepository(session).get_active(knowledge_id)

    async def get_history(self, knowledge_id: KnowledgeId) -> Sequence[KnowledgeEntry]:
        async with self._session_factory() as session:
            return await SqlAlchemyKnowledgeRepository(session).get_history(knowledge_id)

    async def find(self, query: KnowledgeQuery) -> Sequence[KnowledgeEntry]:
        async with self._session_factory() as session:
            return await SqlAlchemyKnowledgeRepository(session).find(query)

    async def get_many_active(
        self, knowledge_ids: Iterable[KnowledgeId]
    ) -> Sequence[KnowledgeEntry]:
        async with self._session_factory() as session:
            return await SqlAlchemyKnowledgeRepository(session).get_many_active(
                knowledge_ids
            )

    async def find_referencing(
        self,
        target: KnowledgeId,
        relation_types: frozenset[RelationType] | None = None,
    ) -> Sequence[KnowledgeEntry]:
        async with self._session_factory() as session:
            return await SqlAlchemyKnowledgeRepository(session).find_referencing(
                target, relation_types
            )
