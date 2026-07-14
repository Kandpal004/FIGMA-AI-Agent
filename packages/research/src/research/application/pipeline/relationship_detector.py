"""RelationshipDetector — stage 8: resolve candidate relationships into edges.

Maps each :class:`CandidateRelationship` (which references entities by *label*) onto
a domain :class:`Relationship` between the corresponding :class:`Entity` ids. A
candidate whose endpoints cannot both be resolved, or that would be a self-loop, is
dropped. Deterministic.
"""

from __future__ import annotations

from collections.abc import Sequence

from research.domain.collection.extraction import RawExtraction
from research.domain.entity.entity import Entity
from research.domain.entity.relationship import Relationship
from research.domain.evidence.evidence import Evidence
from research.domain.shared.ids import EntityId, RelationshipId

__all__ = ["RelationshipDetector"]


class RelationshipDetector:
    """Resolves candidate relationships into typed entity edges."""

    def detect(
        self,
        entities: Sequence[Entity],
        extraction: RawExtraction,
        evidence: Sequence[Evidence],
    ) -> tuple[Relationship, ...]:
        by_label: dict[str, EntityId] = {}
        for entity in entities:
            by_label.setdefault(entity.label.strip().lower(), entity.id)
        evidence_ids = tuple(e.id for e in evidence)

        relationships: list[Relationship] = []
        for candidate in extraction.relationships:
            source_id = by_label.get(candidate.source_label.strip().lower())
            target_id = by_label.get(candidate.target_label.strip().lower())
            if source_id is None or target_id is None or source_id == target_id:
                continue
            relationships.append(
                Relationship(
                    id=RelationshipId.new(),
                    type=candidate.type,
                    source=source_id,
                    target=target_id,
                    confidence=candidate.confidence,
                    evidence_ids=evidence_ids,
                )
            )
        return tuple(relationships)
