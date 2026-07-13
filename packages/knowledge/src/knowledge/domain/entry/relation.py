"""Typed relationships — the edges that make the corpus a reasoning graph.

A flat list of entries cannot answer *"why should this exist?"*. A graph can: an
entry is justified by the entries that ``SUPPORT`` it, refined by those that
``REFINE`` it, and challenged by those that ``CONTRADICT`` it. These typed edges
are what the reasoner traverses to build a cited rationale and to surface
conflicts.

Every edge points at a :class:`~knowledge.domain.shared.ids.KnowledgeId` (a stable
lineage), never at a specific version, so the graph survives re-versioning.

Pure domain: standard library, shared-kernel error base, and knowledge ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from knowledge.domain.shared.ids import KnowledgeId, RelationId

__all__ = [
    "CONFLICTING_RELATIONS",
    "SUPPORTING_RELATIONS",
    "InvalidRelationError",
    "KnowledgeRelation",
    "RelationType",
]


class RelationType(str, Enum):
    """The kind of relationship one entry has to another.

    * ``SUPPORTS``     — provides evidence/justification for the target.
    * ``CONTRADICTS``  — asserts something in tension with the target.
    * ``REFINES``      — narrows or specialises the target.
    * ``DEPENDS_ON``   — is only valid when the target holds.
    * ``SUPERSEDES``   — replaces the target (cross-lineage replacement).
    * ``EXAMPLE_OF``   — is a concrete instance of the target principle.
    * ``DERIVED_FROM`` — was derived from the target.
    * ``RELATED_TO``   — a general, untyped association.
    """

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFINES = "refines"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    EXAMPLE_OF = "example_of"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"


#: Relations that positively justify an entry (traversed to build "why").
SUPPORTING_RELATIONS: frozenset[RelationType] = frozenset(
    {
        RelationType.SUPPORTS,
        RelationType.REFINES,
        RelationType.EXAMPLE_OF,
        RelationType.DERIVED_FROM,
    }
)

#: Relations that indicate tension (surfaced as conflicts).
CONFLICTING_RELATIONS: frozenset[RelationType] = frozenset({RelationType.CONTRADICTS})


class InvalidRelationError(DesignDirectorError):
    """Raised when a relation is constructed with invalid data."""

    code = "invalid_relation"
    http_status = 422


@dataclass(frozen=True, slots=True)
class KnowledgeRelation:
    """A typed, directed edge from an entry to another piece of knowledge.

    Attributes:
        id: Edge identity.
        relation_type: The kind of relationship.
        target: The lineage (:class:`KnowledgeId`) the edge points at.
        note: Optional annotation explaining the relationship.
    """

    id: RelationId
    relation_type: RelationType
    target: KnowledgeId
    note: str = ""

    @property
    def is_supporting(self) -> bool:
        """Whether this edge positively justifies the source entry."""
        return self.relation_type in SUPPORTING_RELATIONS

    @property
    def is_conflicting(self) -> bool:
        """Whether this edge indicates tension with the target."""
        return self.relation_type in CONFLICTING_RELATIONS
