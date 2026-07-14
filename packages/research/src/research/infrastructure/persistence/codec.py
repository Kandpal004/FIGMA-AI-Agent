"""Codec — serializes a ResearchReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes
through the normal aggregate constructor, so a decoded report is re-validated (its
provenance integrity re-checked) — a corrupt document cannot yield an invalid report.

The unified evidence and entity graphs are the union of the results' contents (as the
engine assembles them), so they are rebuilt from the decoded results rather than
stored twice.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from research.domain.entity.entity import Entity
from research.domain.entity.graph import EntityGraph
from research.domain.entity.relationship import Relationship
from research.domain.evidence.evidence import Evidence, EvidenceGraph, SourceRef
from research.domain.report.report import ResearchReport
from research.domain.result.quality import QualityMetrics
from research.domain.result.result import ResearchResult
from research.domain.shared.ids import (
    EntityId,
    EvidenceId,
    RelationshipId,
    ResearchReportId,
    ResearchReportLineageId,
    ResearchResultId,
    ResearchSourceId,
)
from research.domain.shared.value_objects import (
    Completeness,
    Confidence,
    EntityType,
    Freshness,
    ProviderKind,
    QualityScore,
    RelationshipType,
    ResearchCategory,
    Tag,
)
from research.domain.source.source import SourceLocator
from research.domain.validation.issue import IssueSeverity, ValidationIssue

__all__ = ["from_document", "to_document"]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[EvidenceId, ...]:
    return tuple(EvidenceId.from_string(x) for x in raw)


def _locator_doc(loc: SourceLocator) -> dict:
    return {"uri": loc.uri, "selector": loc.selector, "extra": dict(loc.extra)}


def _locator(doc: dict) -> SourceLocator:
    return SourceLocator(
        uri=doc["uri"], selector=doc.get("selector", ""), extra=dict(doc.get("extra", {}))
    )


def _source_ref_doc(ref: SourceRef) -> dict:
    return {
        "source_id": str(ref.source_id),
        "locator": _locator_doc(ref.locator),
        "provider": ref.provider.value,
    }


def _source_ref(doc: dict) -> SourceRef:
    return SourceRef(
        source_id=ResearchSourceId.from_string(doc["source_id"]),
        locator=_locator(doc["locator"]),
        provider=ProviderKind(doc["provider"]),
    )


def _evidence_doc(e: Evidence) -> dict:
    return {
        "id": str(e.id),
        "claim": e.claim,
        "source_ref": _source_ref_doc(e.source_ref),
        "confidence": e.confidence.value,
        "category": e.category.value,
        "snippet": e.snippet,
        "tags": [t.value for t in e.tags],
        "knowledge_id": e.knowledge_id,
    }


def _evidence(doc: dict) -> Evidence:
    return Evidence(
        id=EvidenceId.from_string(doc["id"]),
        claim=doc["claim"],
        source_ref=_source_ref(doc["source_ref"]),
        confidence=Confidence.of(doc["confidence"]),
        category=ResearchCategory(doc["category"]),
        snippet=doc.get("snippet", ""),
        tags=frozenset(Tag.of(t) for t in doc.get("tags", ())),
        knowledge_id=doc.get("knowledge_id"),
    )


def _entity_doc(e: Entity) -> dict:
    return {
        "id": str(e.id),
        "type": e.type.value,
        "label": e.label,
        "confidence": e.confidence.value,
        "attributes": dict(e.attributes),
        "source_refs": [_source_ref_doc(r) for r in e.source_refs],
        "evidence_ids": _ids(e.evidence_ids),
    }


def _entity(doc: dict) -> Entity:
    return Entity(
        id=EntityId.from_string(doc["id"]),
        type=EntityType(doc["type"]),
        label=doc["label"],
        confidence=Confidence.of(doc["confidence"]),
        attributes=dict(doc.get("attributes", {})),
        source_refs=tuple(_source_ref(r) for r in doc.get("source_refs", ())),
        evidence_ids=_eids(doc.get("evidence_ids", ())),
    )


def _relationship_doc(r: Relationship) -> dict:
    return {
        "id": str(r.id),
        "type": r.type.value,
        "source": str(r.source),
        "target": str(r.target),
        "confidence": r.confidence.value,
        "evidence_ids": _ids(r.evidence_ids),
    }


def _relationship(doc: dict) -> Relationship:
    return Relationship(
        id=RelationshipId.from_string(doc["id"]),
        type=RelationshipType(doc["type"]),
        source=EntityId.from_string(doc["source"]),
        target=EntityId.from_string(doc["target"]),
        confidence=Confidence.of(doc["confidence"]),
        evidence_ids=_eids(doc.get("evidence_ids", ())),
    )


def _metrics_doc(m: QualityMetrics) -> dict:
    return {
        "quality_score": m.quality_score.value,
        "freshness": m.freshness.value,
        "completeness": m.completeness.value,
        "confidence": m.confidence.value,
    }


def _metrics(doc: dict) -> QualityMetrics:
    return QualityMetrics(
        quality_score=QualityScore.of(doc["quality_score"]),
        freshness=Freshness(doc["freshness"]),
        completeness=Completeness(doc["completeness"]),
        confidence=Confidence.of(doc["confidence"]),
    )


def _issue_doc(i: ValidationIssue) -> dict:
    return {"severity": i.severity.value, "code": i.code, "message": i.message, "field": i.field}


def _issue(doc: dict) -> ValidationIssue:
    return ValidationIssue(
        severity=IssueSeverity(doc["severity"]),
        code=doc["code"],
        message=doc.get("message", ""),
        field=doc.get("field", ""),
    )


def _result_doc(r: ResearchResult) -> dict:
    return {
        "id": str(r.id),
        "source_id": str(r.source_id),
        "timestamp": r.timestamp.isoformat(),
        "category": r.category.value,
        "metrics": _metrics_doc(r.metrics),
        "version": r.version,
        "evidence": [_evidence_doc(e) for e in r.evidence],
        "entities": [_entity_doc(e) for e in r.entities],
        "relationships": [_relationship_doc(rel) for rel in r.relationships],
        "tags": [t.value for t in r.tags],
        "issues": [_issue_doc(i) for i in r.issues],
    }


def _result(doc: dict) -> ResearchResult:
    return ResearchResult(
        id=ResearchResultId.from_string(doc["id"]),
        source_id=ResearchSourceId.from_string(doc["source_id"]),
        timestamp=datetime.fromisoformat(doc["timestamp"]),
        category=ResearchCategory(doc["category"]),
        metrics=_metrics(doc["metrics"]),
        version=doc.get("version", 1),
        evidence=tuple(_evidence(e) for e in doc.get("evidence", ())),
        entities=tuple(_entity(e) for e in doc.get("entities", ())),
        relationships=tuple(_relationship(rel) for rel in doc.get("relationships", ())),
        tags=frozenset(Tag.of(t) for t in doc.get("tags", ())),
        issues=tuple(_issue(i) for i in doc.get("issues", ())),
    )


# --------------------------- serialize ---------------------------------- #
def to_document(r: ResearchReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "project_id": r.project_id,
        "goal": r.goal,
        "quality": _metrics_doc(r.quality),
        "created_at": r.created_at.isoformat(),
        "results": [_result_doc(res) for res in r.results],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> ResearchReport:
    results = tuple(_result(res) for res in doc["results"])

    evidence: dict[EvidenceId, Evidence] = {}
    entities: dict[EntityId, Entity] = {}
    relationships: list[Relationship] = []
    for res in results:
        for e in res.evidence:
            evidence.setdefault(e.id, e)
        for ent in res.entities:
            entities.setdefault(ent.id, ent)
        relationships.extend(res.relationships)

    return ResearchReport(
        id=ResearchReportId.from_string(doc["id"]),
        lineage_id=ResearchReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"],
        project_id=doc["project_id"],
        goal=doc["goal"],
        results=results,
        evidence_graph=EvidenceGraph.of(evidence.values()),
        entity_graph=EntityGraph.of(entities.values(), relationships),
        quality=_metrics(doc["quality"]),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
