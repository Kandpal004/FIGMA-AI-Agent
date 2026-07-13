"""Serializable view DTOs — the read models the inbound layer returns.

Callers (agents, the Director, an API, a future MCP tool) must never receive raw
domain aggregates. These frozen, primitive-typed projections are the wire shape of
an entry, a citation, a rationale, and a query result — ready to be JSON-encoded.
Pure data with ``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from knowledge.application.query_service import Neighborhood
from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.reasoning.query import QueryResult
from knowledge.domain.reasoning.rationale import Citation, Conflict, Rationale

__all__ = [
    "CitationView",
    "ConflictView",
    "EntryView",
    "NeighborhoodView",
    "QueryResultView",
    "RationaleView",
]


def _iso(value: datetime) -> str:
    return value.isoformat()


@dataclass(frozen=True, slots=True)
class EntryView:
    """A flat projection of a knowledge entry version."""

    entry_version_id: str
    knowledge_id: str
    version: int
    scope: str
    category: str
    subcategory: str | None
    title: str
    statement: str
    description: str
    status: str
    priority: int
    confidence_score: float
    confidence_level: str
    source_name: str
    tags: list[str]
    platforms: list[str]
    page_types: list[str]
    component_types: list[str]
    relations: list[dict[str, str]]
    references: list[dict[str, object]]
    created_at: str
    updated_at: str

    @classmethod
    def from_entry(cls, entry: KnowledgeEntry) -> EntryView:
        app = entry.applicability
        return cls(
            entry_version_id=str(entry.id),
            knowledge_id=str(entry.knowledge_id),
            version=entry.version,
            scope="global" if entry.scope.is_global else "tenant",
            category=entry.category.value,
            subcategory=entry.subcategory.value if entry.subcategory else None,
            title=entry.title,
            statement=entry.statement,
            description=entry.description,
            status=entry.status.value,
            priority=int(entry.priority),
            confidence_score=entry.confidence.score,
            confidence_level=entry.confidence.level.value,
            source_name=entry.source.name,
            tags=sorted(t.value for t in entry.tags),
            platforms=sorted(p.value for p in app.platforms),
            page_types=sorted(app.page_types),
            component_types=sorted(app.component_types),
            relations=[
                {"type": r.relation_type.value, "target": str(r.target)}
                for r in entry.relations
            ],
            references=[
                {"title": ref.title, "kind": ref.kind.value, "url": ref.url}
                for ref in entry.references
            ],
            created_at=_iso(entry.created_at),
            updated_at=_iso(entry.updated_at),
        )


@dataclass(frozen=True, slots=True)
class CitationView:
    """A flat projection of a citation."""

    knowledge_id: str
    entry_version_id: str
    category: str
    title: str
    statement: str
    confidence_score: float
    priority: int
    source_name: str
    why: str
    weight: float

    @classmethod
    def from_citation(cls, citation: Citation) -> CitationView:
        return cls(
            knowledge_id=str(citation.knowledge_id),
            entry_version_id=str(citation.entry_version_id),
            category=citation.category.value,
            title=citation.title,
            statement=citation.statement,
            confidence_score=citation.confidence.score,
            priority=int(citation.priority),
            source_name=citation.source_name,
            why=citation.why,
            weight=citation.weight,
        )


@dataclass(frozen=True, slots=True)
class ConflictView:
    """A flat projection of a resolved conflict."""

    winner: CitationView
    loser: CitationView
    note: str

    @classmethod
    def from_conflict(cls, conflict: Conflict) -> ConflictView:
        return cls(
            winner=CitationView.from_citation(conflict.winner),
            loser=CitationView.from_citation(conflict.loser),
            note=conflict.note,
        )


@dataclass(frozen=True, slots=True)
class RationaleView:
    """A flat projection of a rationale — the cited answer."""

    summary: str
    aggregate_confidence: float
    primary: CitationView | None
    citations: list[CitationView]
    conflicts: list[ConflictView]

    @classmethod
    def from_rationale(cls, rationale: Rationale) -> RationaleView:
        return cls(
            summary=rationale.summary,
            aggregate_confidence=rationale.aggregate_confidence,
            primary=(
                CitationView.from_citation(rationale.primary)
                if rationale.primary
                else None
            ),
            citations=[CitationView.from_citation(c) for c in rationale.citations],
            conflicts=[ConflictView.from_conflict(c) for c in rationale.conflicts],
        )


@dataclass(frozen=True, slots=True)
class QueryResultView:
    """A flat projection of a query result."""

    entries: list[EntryView]
    total: int

    @classmethod
    def from_result(cls, result: QueryResult) -> QueryResultView:
        return cls(
            entries=[EntryView.from_entry(e) for e in result.entries],
            total=result.total,
        )


@dataclass(frozen=True, slots=True)
class NeighborhoodView:
    """A flat projection of an entry's graph neighbourhood."""

    entry: EntryView
    supporting: list[EntryView]
    contradicting: list[EntryView]

    @classmethod
    def from_neighborhood(cls, neighborhood: Neighborhood) -> NeighborhoodView:
        return cls(
            entry=EntryView.from_entry(neighborhood.entry),
            supporting=[EntryView.from_entry(e) for e in neighborhood.supporting],
            contradicting=[EntryView.from_entry(e) for e in neighborhood.contradicting],
        )
