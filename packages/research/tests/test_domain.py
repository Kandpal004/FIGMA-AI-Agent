"""Domain tests — the invariants that make a report trustworthy by construction."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from research.domain.entity.entity import Entity
from research.domain.entity.graph import EntityGraph, InvalidEntityGraphError
from research.domain.entity.relationship import InvalidRelationshipError, Relationship
from research.domain.evidence.evidence import (
    Evidence,
    EvidenceGraph,
    InvalidEvidenceError,
    SourceRef,
)
from research.domain.report.bundle import ReasoningBundle
from research.domain.report.report import InvalidReportError, ResearchReport
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
    QualityBand,
    QualityScore,
    RelationshipType,
    ResearchCategory,
)
from research.domain.source.source import SourceLocator

NOW = datetime(2026, 7, 14, tzinfo=UTC)


# --------------------------- value objects ------------------------------ #
def test_entity_type_has_nineteen_members():
    assert len(EntityType) == 19


def test_confidence_rejects_out_of_range():
    from research.domain.shared.value_objects import InvalidResearchValueError

    with pytest.raises(InvalidResearchValueError):
        Confidence(1.5)


def test_freshness_from_age_is_deterministic_linear_decay():
    assert Freshness.from_age(0).value == 1.0
    assert Freshness.from_age(15).value == pytest.approx(0.5)
    assert Freshness.from_age(30).value == 0.0
    assert Freshness.from_age(60).value == 0.0


def test_completeness_from_counts():
    assert Completeness.from_counts(0, 3).value == 0.0
    assert Completeness.from_counts(3, 3).value == 1.0
    assert Completeness.from_counts(0, 0).value == 1.0


def test_quality_score_band_thresholds():
    assert QualityScore.of(85).band is QualityBand.EXCELLENT
    assert QualityScore.of(65).band is QualityBand.GOOD
    assert QualityScore.of(45).band is QualityBand.FAIR
    assert QualityScore.of(20).band is QualityBand.POOR


# --------------------------- helpers ------------------------------------ #
def _source_ref() -> SourceRef:
    return SourceRef(
        source_id=ResearchSourceId.new(),
        locator=SourceLocator(uri="https://acme.example"),
        provider=ProviderKind.IN_MEMORY,
    )


def _evidence(claim: str = "A claim") -> Evidence:
    return Evidence(
        id=EvidenceId.new(),
        claim=claim,
        source_ref=_source_ref(),
        confidence=Confidence.of(0.8),
        category=ResearchCategory.WEBSITE,
    )


def _entity(evidence_ids=()) -> Entity:
    return Entity(
        id=EntityId.new(),
        type=EntityType.CTA,
        label="Add to Cart",
        confidence=Confidence.of(0.9),
        evidence_ids=tuple(evidence_ids),
    )


def _metrics() -> QualityMetrics:
    return QualityMetrics(
        quality_score=QualityScore.of(80),
        freshness=Freshness(0.9),
        completeness=Completeness(1.0),
        confidence=Confidence.of(0.85),
    )


# --------------------------- evidence / entity graphs ------------------- #
def test_evidence_claim_must_be_non_empty():
    with pytest.raises(InvalidEvidenceError):
        Evidence(
            id=EvidenceId.new(),
            claim="  ",
            source_ref=_source_ref(),
            confidence=Confidence.of(0.5),
            category=ResearchCategory.WEBSITE,
        )


def test_evidence_graph_rejects_duplicate_ids():
    e = _evidence()
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


def test_relationship_rejects_self_loop():
    eid = EntityId.new()
    with pytest.raises(InvalidRelationshipError):
        Relationship(
            id=RelationshipId.new(),
            type=RelationshipType.RELATED_TO,
            source=eid,
            target=eid,
            confidence=Confidence.of(0.5),
        )


def test_entity_graph_rejects_dangling_edge():
    a = _entity()
    rel = Relationship(
        id=RelationshipId.new(),
        type=RelationshipType.RELATED_TO,
        source=a.id,
        target=EntityId.new(),  # not in the graph
        confidence=Confidence.of(0.5),
    )
    with pytest.raises(InvalidEntityGraphError):
        EntityGraph.of([a], [rel])


# --------------------------- report provenance -------------------------- #
def _report(results, evidence, entities, relationships=()) -> ResearchReport:
    return ResearchReport(
        id=ResearchReportId.new(),
        lineage_id=ResearchReportLineageId.new(),
        version=1,
        project_id="proj",
        goal="goal",
        results=tuple(results),
        evidence_graph=EvidenceGraph.of(evidence),
        entity_graph=EntityGraph.of(entities, relationships),
        quality=_metrics(),
        created_at=NOW,
    )


def _result(evidence=(), entities=(), relationships=()) -> ResearchResult:
    return ResearchResult(
        id=ResearchResultId.new(),
        source_id=ResearchSourceId.new(),
        timestamp=NOW,
        category=ResearchCategory.WEBSITE,
        metrics=_metrics(),
        evidence=tuple(evidence),
        entities=tuple(entities),
        relationships=tuple(relationships),
    )


def test_report_accepts_a_fully_attributed_graph():
    e = _evidence()
    ent = _entity(evidence_ids=[e.id])
    result = _result(evidence=[e], entities=[ent])
    report = _report([result], [e], [ent])
    assert report.is_usable
    assert report.evidence_count() == 1
    assert report.entity_count() == 1


def test_report_rejects_dangling_evidence_reference():
    e = _evidence()
    ent = _entity(evidence_ids=[EvidenceId.new()])  # cites missing evidence
    result = _result(evidence=[e], entities=[ent])
    with pytest.raises(InvalidReportError):
        _report([result], [e], [ent])


def test_report_rejects_dangling_entity_reference_from_relationship():
    e = _evidence()
    a = _entity(evidence_ids=[e.id])
    b = _entity(evidence_ids=[e.id])
    rel = Relationship(
        id=RelationshipId.new(),
        type=RelationshipType.RELATED_TO,
        source=a.id,
        target=b.id,
        confidence=Confidence.of(0.6),
    )
    # result references relationship endpoints a and b, but graph only carries a.
    result = _result(evidence=[e], entities=[a, b], relationships=[rel])
    with pytest.raises((InvalidReportError, InvalidEntityGraphError)):
        _report([result], [e], [a], [rel])


def test_report_version_must_be_positive():
    e = _evidence()
    with pytest.raises(InvalidReportError):
        ResearchReport(
            id=ResearchReportId.new(),
            lineage_id=ResearchReportLineageId.new(),
            version=0,
            project_id="proj",
            goal="goal",
            results=(),
            evidence_graph=EvidenceGraph.of([e]),
            entity_graph=EntityGraph.empty(),
            quality=_metrics(),
            created_at=NOW,
        )


def test_reasoning_bundle_projects_report():
    e = _evidence()
    ent = _entity(evidence_ids=[e.id])
    report = _report([_result(evidence=[e], entities=[ent])], [e], [ent])
    bundle = ReasoningBundle.from_report(report)
    assert bundle.report_id == report.id
    assert not bundle.is_empty
    assert len(bundle.evidence) == 1
    assert len(bundle.entities) == 1
