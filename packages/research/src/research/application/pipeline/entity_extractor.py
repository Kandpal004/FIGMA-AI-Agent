"""EntityExtractor — stage 7: turn extraction candidates into typed entities.

Maps each :class:`CandidateEntity` into a domain :class:`Entity`, de-duplicating by
(type, normalized label) within the artifact, attaching the source ref, and linking
the entity to the artifact's evidence (so every entity is grounded and the report's
provenance integrity holds). Deterministic.
"""

from __future__ import annotations

from collections.abc import Sequence

from research.domain.collection.artifact import RawArtifact
from research.domain.collection.extraction import RawExtraction
from research.domain.entity.entity import Entity
from research.domain.evidence.evidence import Evidence, SourceRef
from research.domain.shared.ids import EntityId
from research.domain.source.source import ResearchSource

__all__ = ["EntityExtractor"]


class EntityExtractor:
    """Builds typed entities from extraction candidates."""

    def extract(
        self,
        artifact: RawArtifact,
        source: ResearchSource,
        extraction: RawExtraction,
        evidence: Sequence[Evidence],
    ) -> tuple[Entity, ...]:
        source_ref = SourceRef(
            source_id=source.id, locator=artifact.locator, provider=source.provider
        )
        evidence_ids = tuple(e.id for e in evidence)

        entities: list[Entity] = []
        seen: set[tuple[str, str]] = set()
        for candidate in extraction.entities:
            key = (candidate.type.value, candidate.label.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            entities.append(
                Entity(
                    id=EntityId.new(),
                    type=candidate.type,
                    label=candidate.label,
                    confidence=candidate.confidence,
                    attributes=candidate.attributes,
                    source_refs=(source_ref,),
                    evidence_ids=evidence_ids,
                )
            )
        return tuple(entities)
