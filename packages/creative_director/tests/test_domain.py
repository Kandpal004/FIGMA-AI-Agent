"""Unit tests for the Creative Director domain — the invariants that make a ruling trustworthy."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from creative_director.domain.decision.approval import ApprovalDecision, InvalidApprovalError
from creative_director.domain.decision.history import DecisionHistory, DecisionRecord
from creative_director.domain.evidence.evidence import (
    CDEvidence,
    EvidenceGraph,
    InvalidEvidenceError,
)
from creative_director.domain.finding.finding import Finding
from creative_director.domain.graph.cd_graph import CDEdge, CDGraph, CDNode, InvalidCDGraphError
from creative_director.domain.policy.profile import InvalidProfileError, ReviewProfile
from creative_director.domain.quality.quality import ReviewQualityMetrics
from creative_director.domain.review.dimension_review import (
    DimensionReview,
    InvalidDimensionReviewError,
)
from creative_director.domain.scoring.category_score import CategoryScore
from creative_director.domain.scoring.scorecard import InvalidScorecardError, Scorecard
from creative_director.domain.shared.ids import (
    CDEdgeId,
    CDEvidenceId,
    CDNodeId,
    DecisionId,
    DimensionReviewId,
    FindingId,
)
from creative_director.domain.shared.value_objects import (
    ApprovalStatus,
    Confidence,
    DeciderRole,
    FindingSeverity,
    GraphKind,
    GraphRelation,
    NodeKind,
    Percentage,
    ProvenanceKind,
    ReviewDimension,
    ReviewProfileKind,
    Score,
    ScoreCategory,
    Verdict,
    Weight,
)

_NOW = datetime(2026, 7, 14, tzinfo=UTC)


def test_dimension_and_category_cardinality() -> None:
    assert len(ReviewDimension) == 16
    assert len(ScoreCategory) == 15
    assert len(GraphKind) == 5


@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_confidence_range(bad: float) -> None:
    with pytest.raises(Exception):
        Confidence(bad)


def test_score_band() -> None:
    assert Score(85).band.value == "excellent"
    assert Score(30).band.value == "poor"


# --- evidence ------------------------------------------------------------- #

def _ev(ref: str) -> CDEvidence:
    return CDEvidence(id=CDEvidenceId.new(), provenance=ProvenanceKind.WIREFRAME,
                      external_ref=ref, claim=f"c {ref}", confidence=Confidence(0.8))


def test_evidence_graph_missing_and_duplicate() -> None:
    e = _ev("e1")
    g = EvidenceGraph.of([e])
    absent = CDEvidenceId.new()
    assert g.missing([e.id]) == () and g.missing([absent]) == (absent,)
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --- graph ---------------------------------------------------------------- #

def _node() -> CDNode:
    return CDNode(id=CDNodeId.new(), kind=NodeKind.DIMENSION, label="d")


def test_graph_is_acyclic() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidCDGraphError):
        CDGraph.of(GraphKind.DECISION, [a, b], [
            CDEdge(id=CDEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.INFORMS),
            CDEdge(id=CDEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.INFORMS),
        ])


def test_graph_rejects_dangling_edge() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidCDGraphError):
        CDGraph.of(GraphKind.REVIEW, [a], [
            CDEdge(id=CDEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.RAISES),
        ])


# --- dimension review ----------------------------------------------------- #

def test_failing_dimension_requires_a_finding() -> None:
    with pytest.raises(InvalidDimensionReviewError):
        DimensionReview(
            id=DimensionReviewId.new(), dimension=ReviewDimension.TRUST_SIGNALS,
            verdict=Verdict.FAIL, quality_score=Score(30), confidence=Confidence(0.6),
            notes="failing but no findings", findings=(),
        )


def test_finding_dimension_must_match_review() -> None:
    finding = Finding(id=FindingId.new(), dimension=ReviewDimension.UX_QUALITY,
                      severity=FindingSeverity.BLOCKING, statement="x")
    with pytest.raises(InvalidDimensionReviewError):
        DimensionReview(
            id=DimensionReviewId.new(), dimension=ReviewDimension.TRUST_SIGNALS,
            verdict=Verdict.FAIL, quality_score=Score(30), confidence=Confidence(0.6),
            notes="mismatch", findings=(finding,),
        )


# --- scorecard ------------------------------------------------------------ #

def test_scorecard_requires_overall() -> None:
    cs = CategoryScore(category=ScoreCategory.BUSINESS, score=Score(80), weight=Weight(1.0))
    with pytest.raises(InvalidScorecardError):
        Scorecard.of([cs])


def test_scorecard_overall_and_weakest() -> None:
    scores = [
        CategoryScore(category=ScoreCategory.BUSINESS, score=Score(80), weight=Weight(0.5)),
        CategoryScore(category=ScoreCategory.TRUST, score=Score(40), weight=Weight(0.5)),
        CategoryScore(category=ScoreCategory.OVERALL, score=Score(60), weight=Weight(1.0)),
    ]
    sc = Scorecard.of(scores)
    assert sc.overall.value == 60.0
    assert sc.weakest().category is ScoreCategory.TRUST


# --- approval decision ---------------------------------------------------- #

def test_approved_cannot_cite_failing_gate() -> None:
    with pytest.raises(InvalidApprovalError):
        ApprovalDecision(
            id=DecisionId.new(), status=ApprovalStatus.APPROVED, rationale="ok",
            decided_by=DeciderRole.SYSTEM, decided_at=_NOW, overall_score=Score(80),
            failing_gates=(ScoreCategory.TRUST,),
        )


def test_approval_requires_rationale() -> None:
    with pytest.raises(InvalidApprovalError):
        ApprovalDecision(
            id=DecisionId.new(), status=ApprovalStatus.REJECTED, rationale="  ",
            decided_by=DeciderRole.SYSTEM, decided_at=_NOW, overall_score=Score(20),
        )


# --- decision history ----------------------------------------------------- #

def test_decision_history_append_and_current() -> None:
    r1 = DecisionRecord(decision_id=DecisionId.new(), status=ApprovalStatus.CHANGES_REQUESTED,
                        decided_by=DeciderRole.SYSTEM, decided_at=_NOW, rationale="v1", version=1)
    r2 = DecisionRecord(decision_id=DecisionId.new(), status=ApprovalStatus.APPROVED,
                        decided_by=DeciderRole.CREATIVE_DIRECTOR, decided_at=_NOW,
                        rationale="override", version=2)
    history = DecisionHistory.of([r1]).append(r2)
    assert len(history) == 2
    assert history.current().version == 2
    assert history.overrides()[0].decided_by is DeciderRole.CREATIVE_DIRECTOR


# --- profile & quality ---------------------------------------------------- #

def test_profile_weights_must_sum_to_one() -> None:
    with pytest.raises(InvalidProfileError):
        ReviewProfile(kind=ReviewProfileKind.STARTUP,
                      weights={ScoreCategory.BUSINESS: Weight(0.3), ScoreCategory.TRUST: Weight(0.3)})


def test_review_quality_weighting() -> None:
    q = ReviewQualityMetrics(coverage=Percentage(1.0), grounding=Percentage(1.0),
                             confidence=Confidence(0.5))
    # 0.4*1 + 0.4*1 + 0.2*0.5 = 0.9 → 90
    assert q.overall_score.value == pytest.approx(90.0)
    assert q.is_fully_grounded
