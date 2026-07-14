"""Serializable view DTOs — the review projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They
project a :class:`CreativeDirectorReview` (and the neutral :class:`ApprovalBundle`) into plain
``dict``-friendly structures an API, the orchestration layer, or a console can serialize —
carrying the full review (dimension verdicts, findings, scores, the decision and its history,
the matrices, and the five graphs) but no domain objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from creative_director.domain.decision.history import DecisionHistory
from creative_director.domain.finding.finding import Finding, RequiredChange
from creative_director.domain.graph.cd_graph import CDGraph
from creative_director.domain.matrix.improvement_matrix import ImprovementMatrix
from creative_director.domain.matrix.quality_matrix import QualityMatrix
from creative_director.domain.report.bundle import ApprovalBundle
from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.decision.approval import ApprovalDecision

__all__ = [
    "ApprovalBundleView",
    "ApprovalView",
    "DimensionView",
    "GraphView",
    "QualityView",
    "ReviewView",
    "ScorecardView",
    "TraceView",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _finding_view(f: Finding) -> dict:
    return {
        "id": str(f.id), "dimension": f.dimension.value, "severity": f.severity.value,
        "statement": f.statement,
        "anti_pattern": (f.anti_pattern.value if f.anti_pattern else None),
        "evidence_ids": _ids(f.evidence_ids),
    }


def _change_view(c: RequiredChange) -> dict:
    return {
        "id": str(c.id), "dimension": c.dimension.value, "description": c.description,
        "priority": int(c.priority), "impact": int(c.impact), "blocking": c.blocking,
        "rank": c.rank, "evidence_ids": _ids(c.evidence_ids),
    }


def _dimension_view(dr: DimensionReview) -> dict:
    return {
        "id": str(dr.id), "dimension": dr.dimension.value, "verdict": dr.verdict.value,
        "quality_score": dr.quality_score.value, "band": dr.quality_score.band.value,
        "confidence": dr.confidence.value, "notes": dr.notes,
        "anti_patterns": [a.value for a in dr.anti_patterns()],
        "blocking_issues": [_finding_view(f) for f in dr.blocking_findings()],
        "warnings": [_finding_view(f) for f in dr.warnings()],
        "recommendations": [_finding_view(f) for f in dr.recommendations()],
        "required_changes": [_change_view(c) for c in dr.required_changes],
        "evidence_ids": _ids(dr.evidence_ids),
    }


def _scorecard_view(sc: Scorecard) -> dict:
    return {
        cs.category.value: {
            "score": cs.score.value, "band": cs.band.value, "weight": cs.weight.value,
            "dimensions": [d.value for d in cs.dimensions],
        }
        for cs in sc.scores
    }


def _approval_view(a: ApprovalDecision) -> dict:
    return {
        "id": str(a.id), "status": a.status.value, "rationale": a.rationale,
        "decided_by": a.decided_by.value, "decided_at": _iso(a.decided_at),
        "overall_score": a.overall_score.value,
        "failing_gates": [g.value for g in a.failing_gates],
        "blocking_finding_ids": _ids(a.blocking_finding_ids),
        "superseded_by": (str(a.superseded_by) if a.superseded_by else None),
    }


def _history_view(h: DecisionHistory) -> list[dict]:
    return [
        {"decision_id": str(r.decision_id), "status": r.status.value,
         "decided_by": r.decided_by.value, "decided_at": _iso(r.decided_at),
         "rationale": r.rationale, "version": r.version}
        for r in h
    ]


def _quality_matrix_view(m: QualityMatrix) -> list[dict]:
    return [
        {"category": c.category.value, "score": c.score.value, "band": c.band.value,
         "weight": c.weight.value}
        for c in m.cells
    ]


def _improvement_matrix_view(m: ImprovementMatrix) -> list[dict]:
    return [_change_view(c) for c in m]


def _graph_view(g: CDGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
                  for e in g.edges],
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    coverage: float
    grounding: float
    confidence: float
    overall_score: float
    band: str
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class DimensionView:
    dimension: dict


@dataclass(frozen=True, slots=True)
class ScorecardView:
    scorecard: dict


@dataclass(frozen=True, slots=True)
class ApprovalView:
    approval: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class ReviewView:
    """The full, flat projection of a Creative Director review."""

    review_id: str
    lineage_id: str
    version: int
    project_id: str
    subject: dict
    policy: dict
    is_approved: bool
    can_proceed: bool
    created_at: str
    quality: QualityView
    scorecard: dict
    approval: dict
    dimension_reviews: list[dict]
    decision_history: list[dict]
    quality_matrix: list[dict]
    improvement_matrix: list[dict]
    graphs: dict
    dimension_count: int
    evidence_count: int

    @classmethod
    def from_review(cls, review: CreativeDirectorReview) -> ReviewView:
        quality = QualityView(
            coverage=review.quality.coverage.value, grounding=review.quality.grounding.value,
            confidence=review.quality.confidence.value,
            overall_score=review.quality.overall_score.value, band=review.quality.band.value,
            is_fully_grounded=review.quality.is_fully_grounded,
        )
        return cls(
            review_id=str(review.id), lineage_id=str(review.lineage_id), version=review.version,
            project_id=review.project_id,
            subject={"kind": review.subject.kind.value, "reference": review.subject.reference,
                     "label": review.subject.label, "phase": review.subject.phase},
            policy={"profile": review.policy.profile.kind.value, "mode": review.policy.mode.value,
                    "threshold": review.policy.effective_threshold.value},
            is_approved=review.is_approved, can_proceed=review.can_proceed,
            created_at=_iso(review.created_at), quality=quality,
            scorecard=_scorecard_view(review.scorecard),
            approval=_approval_view(review.approval),
            dimension_reviews=[_dimension_view(dr) for dr in review.dimension_reviews],
            decision_history=_history_view(review.decision_history),
            quality_matrix=_quality_matrix_view(review.quality_matrix),
            improvement_matrix=_improvement_matrix_view(review.improvement_matrix),
            graphs={g.kind.value: _graph_view(g) for g in review.graphs.all()},
            dimension_count=review.dimension_count(), evidence_count=review.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class ApprovalBundleView:
    """The neutral ruling a downstream phase acts on."""

    review_id: str
    project_id: str
    subject_reference: str
    status: str
    can_proceed: bool
    overall_score: float
    required_changes: list[dict]
    created_at: str

    @classmethod
    def from_bundle(cls, b: ApprovalBundle) -> ApprovalBundleView:
        return cls(
            review_id=str(b.review_id), project_id=b.project_id,
            subject_reference=b.subject_reference, status=b.status.value,
            can_proceed=b.can_proceed, overall_score=b.overall_score.value,
            required_changes=[_change_view(c) for c in b.required_changes],
            created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class TraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
