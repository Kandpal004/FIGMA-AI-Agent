"""Relationships — typed edges between extracted entities.

A :class:`Relationship` connects two entities with a typed edge (``Section CONTAINS
CTA``, ``Product HAS_PRICING Pricing``, ``Navigation LINKS_TO Category``), carrying a
confidence and the evidence that supports it. Self-loops are rejected.

Pure domain: standard library, the shared-kernel error base, research ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from research.domain.shared.ids import EntityId, EvidenceId, RelationshipId
from research.domain.shared.value_objects import Confidence, RelationshipType

__all__ = ["InvalidRelationshipError", "Relationship"]


class InvalidRelationshipError(DesignDirectorError):
    """Raised when a relationship is constructed with invalid data."""

    code = "invalid_relationship"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Relationship:
    """A typed, directed edge between two entities.

    Attributes:
        id: Relationship identity.
        type: The relationship type.
        source: The source entity.
        target: The target entity.
        confidence: Confidence in the relationship.
        evidence_ids: The evidence supporting it.
    """

    id: RelationshipId
    type: RelationshipType
    source: EntityId
    target: EntityId
    confidence: Confidence
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidRelationshipError(
                "Relationship cannot connect an entity to itself.",
                details={"entity": str(self.source)},
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
