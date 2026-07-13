"""PostgreSQL-backed memory store (structured recall).

Implements :class:`~director.application.ports.memory_port.MemoryStore` over the
``director_memory_records`` table. It provides durable, scope-filtered recall of
memory records — the structured half of the Memory Engine's remit (Principle
P8/P11).

Semantic ranking by ``query`` (vector similarity, Qdrant) is a *separate* adapter
behind this same port: because the application depends only on the port, a Qdrant
semantic store — or a composite that consults both — can be swapped in without any
change to the Memory Engine or the Director. This store honours the ``query``
parameter by returning scope-and-kind matches most-recent-first; it does not
attempt vector ranking, which is that other adapter's job.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from director.domain.memory.entities import MemoryKind, MemoryRecord, MemoryScope
from director.infrastructure.persistence import mappers
from director.infrastructure.persistence.models import MemoryRecordModel

__all__ = ["PostgresMemoryStore"]


class PostgresMemoryStore:
    """Durable, scope-filtered structured memory over Postgres."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def remember(self, record: MemoryRecord) -> None:
        async with self._session_factory() as session:
            session.add(mappers.memory_to_model(record))
            await session.commit()

    async def recall(
        self,
        scope: MemoryScope,
        *,
        kinds: Sequence[MemoryKind] | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Sequence[MemoryRecord]:
        stmt = select(MemoryRecordModel).where(
            MemoryRecordModel.project_id == scope.project_id.value
        )
        if scope.section_id is not None:
            # Section recall: this section's memories plus project-wide ones.
            stmt = stmt.where(
                (MemoryRecordModel.section_id == scope.section_id.value)
                | (MemoryRecordModel.section_id.is_(None))
            )
        # Project-wide recall (section_id None) includes every record in the
        # project, so no additional section filter is applied.

        if kinds:
            stmt = stmt.where(MemoryRecordModel.kind.in_([k.value for k in kinds]))

        stmt = stmt.order_by(MemoryRecordModel.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [mappers.model_to_memory(m) for m in result.scalars().all()]
