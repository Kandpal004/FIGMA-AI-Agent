"""The semantic search port — the future Qdrant seam.

Semantic search is a *discovery aid layered on top of* the structured corpus,
never its source of truth (see the Phase-3 architecture). This port expresses
that role: given free text, return **candidate lineages** (:class:`KnowledgeId` s)
that are then re-fetched and re-ranked through the structured repository, so the
authoritative filtering and ordering stay deterministic.

A real, structured keyword implementation ships now (over the in-memory and SQL
stores); a Qdrant-backed vector implementation can replace it later behind this
same interface, with no change to the application. If search is unavailable, the
query service simply falls back to structured retrieval — no loss of correctness.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from knowledge.domain.shared.ids import KnowledgeId
from knowledge.domain.taxonomy.category import KnowledgeCategory

__all__ = ["KnowledgeSearchPort"]


@runtime_checkable
class KnowledgeSearchPort(Protocol):
    """Returns candidate knowledge lineages for a free-text query."""

    async def search(
        self,
        text: str,
        *,
        categories: Sequence[KnowledgeCategory] | None = None,
        limit: int | None = None,
    ) -> Sequence[KnowledgeId]:
        """Return candidate lineages ranked by relevance to ``text``.

        Results are candidates only — the caller resolves them to canonical
        entries and applies authoritative structured ranking.
        """
        ...
