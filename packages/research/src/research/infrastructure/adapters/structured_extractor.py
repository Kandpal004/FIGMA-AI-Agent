"""StructuredExtractor — a deterministic extractor for structured artifacts.

For artifacts whose payload is already structured (JSON produced by internal
sources like the Knowledge Engine or Project Memory, or by a structured provider),
this adapter parses the payload into :class:`RawExtraction` candidates. It is
deterministic and dependency-free (stdlib ``json``); malformed or partial payloads
degrade gracefully to an empty extraction.

The expected payload shape::

    {
      "entities":      [{"type", "label", "confidence", "attributes"?}],
      "evidence":      [{"claim", "confidence", "category", "snippet"?}],
      "relationships": [{"type", "source_label", "target_label", "confidence"}]
    }
"""

from __future__ import annotations

import json

from research.domain.collection.artifact import RawArtifact
from research.domain.collection.extraction import (
    CandidateEntity,
    CandidateEvidence,
    CandidateRelationship,
    RawExtraction,
)
from research.domain.shared.value_objects import (
    ArtifactKind,
    Confidence,
    EntityType,
    RelationshipType,
    ResearchCategory,
)

__all__ = ["StructuredExtractor"]

_SUPPORTED = {ArtifactKind.STRUCTURED, ArtifactKind.JSON}


class StructuredExtractor:
    """Parses a structured (JSON) artifact payload into extraction candidates."""

    def supports(self, kind: ArtifactKind) -> bool:
        return kind in _SUPPORTED

    async def extract(self, artifact: RawArtifact) -> RawExtraction:
        try:
            data = json.loads(artifact.payload)
        except (json.JSONDecodeError, ValueError):
            return RawExtraction(artifact_id=artifact.id)
        if not isinstance(data, dict):
            return RawExtraction(artifact_id=artifact.id)

        return RawExtraction(
            artifact_id=artifact.id,
            entities=tuple(self._entities(data.get("entities", []))),
            evidence=tuple(self._evidence(data.get("evidence", []))),
            relationships=tuple(self._relationships(data.get("relationships", []))),
        )

    @staticmethod
    def _conf(raw: object, default: float = 0.6) -> Confidence:
        try:
            return Confidence.clamp(float(raw))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return Confidence.of(default)

    def _entities(self, raw):
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                entity_type = EntityType(item["type"])
            except (KeyError, ValueError):
                continue
            label = str(item.get("label", "")).strip()
            if not label:
                continue
            attributes = {
                str(k): str(v) for k, v in (item.get("attributes") or {}).items()
            }
            yield CandidateEntity(
                type=entity_type, label=label, confidence=self._conf(item.get("confidence")),
                attributes=attributes,
            )

    def _evidence(self, raw):
        for item in raw:
            if not isinstance(item, dict):
                continue
            claim = str(item.get("claim", "")).strip()
            if not claim:
                continue
            try:
                category = ResearchCategory(item.get("category", "website"))
            except ValueError:
                category = ResearchCategory.WEBSITE
            yield CandidateEvidence(
                claim=claim, confidence=self._conf(item.get("confidence")),
                category=category, snippet=str(item.get("snippet", "")),
            )

    def _relationships(self, raw):
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                relation_type = RelationshipType(item["type"])
            except (KeyError, ValueError):
                continue
            source_label = str(item.get("source_label", "")).strip()
            target_label = str(item.get("target_label", "")).strip()
            if not source_label or not target_label:
                continue
            yield CandidateRelationship(
                type=relation_type, source_label=source_label, target_label=target_label,
                confidence=self._conf(item.get("confidence")),
            )
