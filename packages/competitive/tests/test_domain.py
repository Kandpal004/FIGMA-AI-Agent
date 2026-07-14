"""Domain-layer tests: value objects, patterns, matrices, and report integrity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from competitive.domain.evidence.evidence import EvidenceGraph, EvidenceRef
from competitive.domain.matrix.benchmark import BenchmarkMatrix
from competitive.domain.matrix.best_practice import BestPracticeMatrix
from competitive.domain.matrix.gap import Gap, GapAnalysis
from competitive.domain.matrix.recommendation import (
    InvalidRecommendationError, Recommendation, RecommendationMatrix)
from competitive.domain.matrix.risk import RiskMatrix
from competitive.domain.matrix.swot import SWOTMatrix
from competitive.domain.pattern.pattern import InvalidPatternError, PatternInstance, RecurringPattern
from competitive.domain.report.report import CompetitorIntelligenceReport, InvalidReportError
from competitive.domain.shared.ids import (
    CompetitorId, EvidenceId, PatternId, RecommendationId, ReportId, ReportLineageId)
from competitive.domain.shared.value_objects import (
    BenchmarkBand, CompetitorDimension as Dim, Confidence, PatternKind, Prevalence,
    RecommendationAction, Score, Severity)

NOW = datetime(2026, 7, 14, tzinfo=UTC)


def _ev(dim=Dim.CONVERSION_PATTERNS):
    return EvidenceRef(id=EvidenceId.new(), knowledge_id="k", entry_version_id="v", category="c",
                       title="T", statement="S", source_name="src", confidence=0.85, dimension=dim)


def test_benchmark_band_relative():
    assert BenchmarkBand.from_relative(Score.of(80), Score.of(70)) is BenchmarkBand.LEADER
    assert BenchmarkBand.from_relative(Score.of(60), Score.of(70)) is BenchmarkBand.PARITY
    assert BenchmarkBand.from_relative(Score.of(30), Score.of(70)) is BenchmarkBand.LAGGARD


def test_prevalence_bands():
    assert Prevalence(3, 4).band.value == "ubiquitous" and Prevalence(3, 4).is_dominant
    assert Prevalence(1, 4).band.value == "emerging"   # 0.25
    assert Prevalence(1, 10).band.value == "rare"      # 0.10
    with pytest.raises(Exception):
        Prevalence(5, 4)


def test_pattern_adopt_requires_evidence():
    e = _ev()
    RecurringPattern.from_instances(
        id=PatternId.new(), kind=PatternKind.CRO, dimension=Dim.CONVERSION_PATTERNS, name="CTA",
        description="d", instances=[PatternInstance(CompetitorId.new(), Dim.CONVERSION_PATTERNS)],
        total_competitors=2, action=RecommendationAction.ADOPT, confidence=Confidence.of(0.8),
        evidence_ids=[e.id])
    with pytest.raises(InvalidPatternError):
        RecurringPattern.from_instances(
            id=PatternId.new(), kind=PatternKind.CRO, dimension=Dim.CONVERSION_PATTERNS, name="X",
            description="d", instances=[], total_competitors=2, action=RecommendationAction.ADOPT,
            confidence=Confidence.of(0.5))


def test_recommendation_requires_evidence():
    e = _ev()
    Recommendation(id=RecommendationId.new(), action=RecommendationAction.ADOPT, dimension=Dim.CONVERSION_PATTERNS,
                   title="t", rationale="r", priority=Severity.HIGH, confidence=Confidence.of(0.8),
                   evidence_ids=[e.id])
    with pytest.raises(InvalidRecommendationError):
        Recommendation(id=RecommendationId.new(), action=RecommendationAction.ADOPT, dimension=Dim.CONVERSION_PATTERNS,
                       title="t", rationale="r", priority=Severity.HIGH, confidence=Confidence.of(0.8))


def test_gap_analysis_index():
    ga = GapAnalysis(gaps=(
        Gap(dimension=Dim.TYPOGRAPHY, client_score=Score.of(40), benchmark_score=Score.of(70), severity=Severity.HIGH),
        Gap(dimension=Dim.SEO, client_score=Score.of(80), benchmark_score=Score.of(70), severity=Severity.LOW)))
    assert ga.overall_gap_index == 15.0 and len(ga.material_gaps()) == 1


def _report(evidence_graph, recommendations):
    return CompetitorIntelligenceReport(
        id=ReportId.new(), lineage_id=ReportLineageId.new(), version=1, industry="beauty", market="",
        country="", business_goals=(), competitors=(), profiles=(), patterns=(),
        benchmark=BenchmarkMatrix(), swot=SWOTMatrix(), gap_analysis=GapAnalysis(),
        best_practices=BestPracticeMatrix(), risk_matrix=RiskMatrix(), recommendations=recommendations,
        evidence_graph=evidence_graph, confidence=Confidence.of(0.8), created_at=NOW)


def test_report_rejects_dangling_evidence():
    orphan = _ev()
    rec = Recommendation(id=RecommendationId.new(), action=RecommendationAction.ADOPT, dimension=Dim.CONVERSION_PATTERNS,
                         title="t", rationale="r", priority=Severity.HIGH, confidence=Confidence.of(0.8),
                         evidence_ids=[orphan.id])
    with pytest.raises(InvalidReportError):
        _report(EvidenceGraph.empty(), RecommendationMatrix(recommendations=(rec,)))


def test_report_accepts_grounded_evidence():
    e = _ev()
    rec = Recommendation(id=RecommendationId.new(), action=RecommendationAction.ADOPT, dimension=Dim.CONVERSION_PATTERNS,
                         title="t", rationale="r", priority=Severity.HIGH, confidence=Confidence.of(0.8),
                         evidence_ids=[e.id])
    report = _report(EvidenceGraph.of([e]), RecommendationMatrix(recommendations=(rec,)))
    assert report.evidence_count() == 1 and report.is_actionable
