"""Memory store port — the interface behind the Memory Engine.

The Memory Engine (an application service) exposes a clean, domain-shaped memory
API to the Director. It delegates the actual storage and retrieval to this
:class:`MemoryStore` port, which the infrastructure layer implements over
PostgreSQL (structured recall) and Qdrant (semantic recall). Keeping this a
Protocol means the application never imports a database or vector-store client.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from director.domain.memory.entities import MemoryKind, MemoryRecord, MemoryScope

__all__ = ["MemoryStore"]


@runtime_checkable
class MemoryStore(Protocol):
    """Persists and retrieves :class:`MemoryRecord` s, scoped by project/section."""

    async def remember(self, record: MemoryRecord) -> None:
        """Persist a memory record."""
        ...

    async def recall(
        self,
        scope: MemoryScope,
        *,
        kinds: Sequence[MemoryKind] | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Sequence[MemoryRecord]:
        """Return records in scope, most relevant first.

        Args:
            scope: The project (and optionally section) to recall for. Records
                whose scope is *covered by* ``scope`` are eligible — a
                project-wide recall includes section memories; a section recall
                includes that section's and the project-wide memories.
            kinds: If given, restrict to these kinds.
            query: If given, a natural-language query for semantic ranking;
                otherwise records are returned by recency/relevance as the
                implementation sees fit.
            limit: Optional cap on the number of records returned.
        """
        ...
