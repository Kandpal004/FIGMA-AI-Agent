"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of a
:class:`ResearchReport` (or a :class:`ReasoningBundle`) — never the domain
aggregate. Pure data with ``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from research.domain.entity.entity import Entity
from research.domain.entity.relationship import Relationship
from research.domain.evidence.evidence import Evidence
from research.domain.report.bundle import ReasoningBundle
from research.domain.report.report import ResearchReport
from research.domain.result.quality import QualityMetrics
from research.domain.result.result import ResearchResult

__all__ = [
    "EntityView",
    "EvidenceTraceView",
    "EvidenceView",
    "QualityView",
    "ReasoningBundleView",
    "RelationshipView",
    "ReportView",
    "ResultView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


@dataclass(frozen=True, slots=True)
class QualityView:
    quality_score: float
    quality_band: str
    freshness: float
    completeness: float
    confidence: float

    @classmethod
    def from_metrics(cls, m: QualityMetrics) -> QualityView:
        return cls(
            quality_score=m.quality_score.value,
            quality_band=m.quality_score.band.value,
            freshness=m.freshness.value,
            completeness=m.completeness.value,
            confidence=m.confidence.value,
        )


@dataclass(frozen=True, slots=True)
class EvidenceView:
    id: str
    claim: str
    category: str
    snippet: str
    confidence: float
    source_id: str
    provider: str
    uri: str
    selector: str
    knowledge_id: str | None
    is_grounded: bool
    tags: list[str]

    @classmethod
    def from_evidence(cls, e: Evidence) -> EvidenceView:
        return cls(
            id=str(e.id),
            claim=e.claim,
            category=e.category.value,
            snippet=e.snippet,
            confidence=e.confidence.value,
            source_id=str(e.source_ref.source_id),
            provider=e.source_ref.provider.value,
            uri=e.source_ref.locator.uri,
            selector=e.source_ref.locator.selector,
            knowledge_id=e.knowledge_id,
            is_grounded=e.is_grounded,
            tags=sorted(t.value for t in e.tags),
        )


@dataclass(frozen=True, slots=True)
class EntityView:
    id: str
    type: str
    label: str
    confidence: float
    attributes: dict[str, str]
    evidence_ids: list[str]

    @classmethod
    def from_entity(cls, e: Entity) -> EntityView:
        return cls(
            id=str(e.id),
            type=e.type.value,
            label=e.label,
            confidence=e.confidence.value,
            attributes=dict(e.attributes),
            evidence_ids=_ids(e.evidence_ids),
        )


@dataclass(frozen=True, slots=True)
class RelationshipView:
    id: str
    type: str
    source: str
    target: str
    confidence: float
    evidence_ids: list[str]

    @classmethod
    def from_relationship(cls, r: Relationship) -> RelationshipView:
        return cls(
            id=str(r.id),
            type=r.type.value,
            source=str(r.source),
            target=str(r.target),
            confidence=r.confidence.value,
            evidence_ids=_ids(r.evidence_ids),
        )


@dataclass(frozen=True, slots=True)
class ResultView:
    id: str
    source_id: str
    category: str
    timestamp: str
    version: int
    quality: QualityView
    evidence: list[EvidenceView]
    entities: list[EntityView]
    relationships: list[RelationshipView]
    tags: list[str]
    issues: list[str]

    @classmethod
    def from_result(cls, r: ResearchResult) -> ResultView:
        return cls(
            id=str(r.id),
            source_id=str(r.source_id),
            category=r.category.value,
            timestamp=_iso(r.timestamp),
            version=r.version,
            quality=QualityView.from_metrics(r.metrics),
            evidence=[EvidenceView.from_evidence(e) for e in r.evidence],
            entities=[EntityView.from_entity(e) for e in r.entities],
            relationships=[RelationshipView.from_relationship(x) for x in r.relationships],
            tags=sorted(t.value for t in r.tags),
            issues=[f"{i.severity.value}:{i.code}" for i in r.issues],
        )


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of a research report."""

    report_id: str
    lineage_id: str
    version: int
    project_id: str
    goal: str
    is_usable: bool
    created_at: str
    quality: QualityView
    source_ids: list[str]
    results: list[ResultView]
    evidence: list[EvidenceView]
    entities: list[EntityView]
    relationships: list[RelationshipView]

    @classmethod
    def from_report(cls, r: ResearchReport) -> ReportView:
        return cls(
            report_id=str(r.id),
            lineage_id=str(r.lineage_id),
            version=r.version,
            project_id=r.project_id,
            goal=r.goal,
            is_usable=r.is_usable,
            created_at=_iso(r.created_at),
            quality=QualityView.from_metrics(r.quality),
            source_ids=_ids(r.sources()),
            results=[ResultView.from_result(res) for res in r.results],
            evidence=[EvidenceView.from_evidence(e) for e in r.all_evidence()],
            entities=[EntityView.from_entity(e) for e in r.all_entities()],
            relationships=[
                RelationshipView.from_relationship(x) for x in r.all_relationships()
            ],
        )


@dataclass(frozen=True, slots=True)
class ReasoningBundleView:
    """The neutral projection downstream engines consume, flattened for transport."""

    report_id: str
    project_id: str
    goal: str
    is_empty: bool
    quality: QualityView
    created_at: str
    evidence: list[EvidenceView]
    entities: list[EntityView]
    relationships: list[RelationshipView]

    @classmethod
    def from_bundle(cls, b: ReasoningBundle) -> ReasoningBundleView:
        return cls(
            report_id=str(b.report_id),
            project_id=b.project_id,
            goal=b.goal,
            is_empty=b.is_empty,
            quality=QualityView.from_metrics(b.quality),
            created_at=_iso(b.created_at),
            evidence=[EvidenceView.from_evidence(e) for e in b.evidence],
            entities=[EntityView.from_entity(e) for e in b.entities],
            relationships=[RelationshipView.from_relationship(x) for x in b.relationships],
        )


@dataclass(frozen=True, slots=True)
class EvidenceTraceView:
    """An explanation of one entity: the entity and the evidence that supports it."""

    entity: EntityView
    evidence: list[EvidenceView]
