"""The Memory Engine — the platform's clean, domain-shaped memory API.

The Memory Engine is what the Director talks to so it "never loses project
context". It exposes a small, intention-revealing API — ``remember`` a fact,
``recall`` facts, ``load_context`` for a project/section — and delegates storage
to the injected :class:`~director.application.ports.memory_port.MemoryStore`
(PostgreSQL for structured recall, Qdrant for semantic recall). Callers never see
the store; they see records and :class:`ProjectContext`.

It is an application service: it orchestrates the port and assembles domain read
models, but performs no storage itself and holds no mutable state.

Testing considerations
----------------------
* :meth:`load_context` returns a :class:`ProjectContext` populated from
  :meth:`MemoryStore.recall`, scoped to the requested project/section.
* :meth:`remember_fact` builds and stores a valid :class:`MemoryRecord`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from director.application.ports.memory_port import MemoryStore
from director.domain.memory.entities import (
    MemoryKind,
    MemoryRecord,
    MemoryScope,
)
from director.domain.project.entities import ProjectContext
from director.domain.shared.ids import MemoryRecordId, ProjectId, SectionId

__all__ = ["MemoryEngine"]


class MemoryEngine:
    """A clean memory API over the :class:`MemoryStore` port."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    # -- writes ------------------------------------------------------------ #
    async def remember(self, record: MemoryRecord) -> None:
        """Persist a memory record."""
        await self._store.remember(record)

    async def remember_fact(
        self,
        scope: MemoryScope,
        kind: MemoryKind,
        *,
        title: str,
        body: str,
        data: Mapping[str, object] | None = None,
        tags: tuple[str, ...] = (),
        source: str = "",
        confidence: float = 1.0,
    ) -> MemoryRecord:
        """Construct and persist a memory record, returning it.

        A convenience so callers do not assemble a :class:`MemoryRecord` by hand.
        """
        record = MemoryRecord(
            id=MemoryRecordId.new(),
            scope=scope,
            kind=kind,
            title=title,
            body=body,
            data=data or {},
            tags=tags,
            source=source,
            confidence=confidence,
        )
        await self._store.remember(record)
        return record

    # -- reads ------------------------------------------------------------- #
    async def recall(
        self,
        scope: MemoryScope,
        *,
        kinds: Sequence[MemoryKind] | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Sequence[MemoryRecord]:
        """Recall records in scope, most relevant first."""
        return await self._store.recall(scope, kinds=kinds, query=query, limit=limit)

    async def load_context(
        self,
        project_id: ProjectId,
        *,
        section_id: SectionId | None = None,
        kinds: Sequence[MemoryKind] | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> ProjectContext:
        """Assemble a :class:`ProjectContext` snapshot for a project (and section).

        For a section-scoped load, the store returns both the section's memories
        and the project-wide ones (per :meth:`MemoryScope.covers`).
        """
        scope = (
            MemoryScope.section(project_id, section_id)
            if section_id is not None
            else MemoryScope.project(project_id)
        )
        records = await self._store.recall(scope, kinds=kinds, query=query, limit=limit)
        return ProjectContext(
            project_id=project_id,
            section_id=section_id,
            records=tuple(records),
        )
