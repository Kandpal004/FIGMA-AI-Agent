"""The Knowledge Link port — grounds research evidence in the Knowledge Engine.

The knowledge-mapping stage asks this port whether a piece of evidence corresponds
to a known principle in the Knowledge Engine (Phase 3); if so, the evidence is
linked to that entry. The adapter behind it wraps Phase 3; the domain never imports
it, and linking is optional (the port may return nothing).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from research.domain.shared.value_objects import ResearchCategory

__all__ = ["KnowledgeLink", "KnowledgeLinkPort"]


@dataclass(frozen=True, slots=True)
class KnowledgeLink:
    """A candidate link between a research finding and a Knowledge entry.

    Attributes:
        knowledge_id: The linked entry's stable lineage id (UUID string).
        entry_version_id: The exact version linked (UUID string).
        title: The entry's title.
        statement: The entry's principle.
        confidence: How strong the link is, in ``[0, 1]``.
    """

    knowledge_id: str
    entry_version_id: str
    title: str
    statement: str
    confidence: float


@runtime_checkable
class KnowledgeLinkPort(Protocol):
    """Finds Knowledge-Engine entries that a research finding corresponds to."""

    async def link(
        self,
        claim: str,
        category: ResearchCategory,
        *,
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[KnowledgeLink]:
        """Return candidate Knowledge links for a claim; empty when none apply."""
        ...
