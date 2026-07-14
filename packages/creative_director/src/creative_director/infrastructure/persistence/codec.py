"""Codec — serializes a CreativeDirectorReview to a JSON document and back.

A review is a deep, immutable aggregate; it is stored and loaded whole as one JSON document.
This codec is the single, exhaustive translation. Reconstruction goes through the normal
aggregate constructor, so a decoded review is re-validated (its provenance, decision, and
graph integrity re-checked) — a corrupt document cannot yield an inconsistent ruling. The
quality and improvement matrices are derived from the decoded scorecard and dimension reviews,
so they can never drift from the material they summarise.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from creative_director.domain.context.context import ReviewSubject
from creative_director.domain.decision.approval import ApprovalDecision
from creative_director.domain.decision.history import DecisionHistory, DecisionRecord
from creative_director.domain.evidence.evidence import CDEvidence, EvidenceGraph
from creative_director.domain.finding.finding import Finding, RequiredChange
from creative_director.domain.graph.cd_graph import CDEdge, CDGraph, CDNode
from creative_director.domain.graph.graphs import CreativeDirectorGraphs
from creative_director.domain.matrix.improvement_matrix import ImprovementMatrix
from creative_director.domain.matrix.quality_matrix import QualityMatrix
from creative_director.domain.policy.policy import ReviewPolicy
from creative_director.domain.policy.profile import ReviewProfile
from creative_director.domain.quality.quality import ReviewQualityMetrics
from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.category_score import CategoryScore
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.ids import (
    CDEdgeId,
    CDEvidenceId,
    CDNodeId,
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
    DecisionId,
    DimensionReviewId,
    FindingId,
    RequiredChangeId,
)
from creative_director.domain.shared.value_objects import (
    AntiPattern,
    ApprovalStatus,
    Confidence,
    DeciderRole,
    FindingSeverity,
    GraphKind,
    GraphRelation,
    NodeKind,
    Percentage,
    Priority,
    ProvenanceKind,
    ReviewDimension,
    ReviewMode,
    ReviewProfileKind,
    Score,
    ScoreCategory,
    SubjectKind,
    Tag,
    Verdict,
    Weight,
)

__all__ = ["from_document", "to_document"]


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def _finding_doc(f: Finding) -> dict:
    return {
        "id": str(f.id), "dimension": f.dimension.value, "severity": f.severity.value,
        "statement": f.statement,
        "anti_pattern": (f.anti_pattern.value if f.anti_pattern else None),
        "evidence_ids": _ids(f.evidence_ids),
    }


def _change_doc(c: RequiredChange) -> dict:
    return {
        "id": str(c.id), "dimension": c.dimension.value, "description": c.description,
        "priority": int(c.priority), "impact": int(c.impact), "blocking": c.blocking,
        "evidence_ids": _ids(c.evidence_ids),
    }


def _dimension_doc(dr: DimensionReview) -> dict:
    return {
        "id": str(dr.id), "dimension": dr.dimension.value, "verdict": dr.verdict.value,
        "quality_score": dr.quality_score.value, "confidence": dr.confidence.value,
        "notes": dr.notes,
        "findings": [_finding_doc(f) for f in dr.findings],
        "required_changes": [_change_doc(c) for c in dr.required_changes],
        "evidence_ids": _ids(dr.evidence_ids),
    }


def _profile_doc(p: ReviewProfile) -> dict:
    return {
        "kind": p.kind.value,
        "weights": {c.value: w.value for c, w in p.weights.items()},
        "hard_gates": {c.value: s.value for c, s in p.hard_gates.items()},
        "default_threshold": p.default_threshold.value,
    }


def _policy_doc(p: ReviewPolicy) -> dict:
    return {
        "profile": _profile_doc(p.profile), "mode": p.mode.value,
        "threshold_override": (p.threshold_override.value if p.threshold_override else None),
    }


def _score_doc(cs: CategoryScore) -> dict:
    return {
        "category": cs.category.value, "score": cs.score.value, "weight": cs.weight.value,
        "dimensions": [d.value for d in cs.dimensions], "evidence_ids": _ids(cs.evidence_ids),
    }


def _approval_doc(a: ApprovalDecision) -> dict:
    return {
        "id": str(a.id), "status": a.status.value, "rationale": a.rationale,
        "decided_by": a.decided_by.value, "decided_at": a.decided_at.isoformat(),
        "overall_score": a.overall_score.value,
        "failing_gates": [g.value for g in a.failing_gates],
        "blocking_finding_ids": _ids(a.blocking_finding_ids),
        "superseded_by": (str(a.superseded_by) if a.superseded_by else None),
        "evidence_ids": _ids(a.evidence_ids),
    }


def _record_doc(r: DecisionRecord) -> dict:
    return {
        "decision_id": str(r.decision_id), "status": r.status.value,
        "decided_by": r.decided_by.value, "decided_at": r.decided_at.isoformat(),
        "rationale": r.rationale, "version": r.version,
    }


def _graph_doc(g: CDGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


def _evidence_doc(e: CDEvidence) -> dict:
    return {
        "id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
        "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
        "source_name": e.source_name, "tags": sorted(t.value for t in e.tags),
    }


def to_document(review: CreativeDirectorReview) -> dict:
    """Serialize a review to a JSON-safe document."""
    return {
        "id": str(review.id), "lineage_id": str(review.lineage_id), "version": review.version,
        "project_id": review.project_id, "created_at": review.created_at.isoformat(),
        "subject": {"kind": review.subject.kind.value, "reference": review.subject.reference,
                    "label": review.subject.label, "phase": review.subject.phase},
        "policy": _policy_doc(review.policy),
        "dimension_reviews": [_dimension_doc(dr) for dr in review.dimension_reviews],
        "scorecard": [_score_doc(cs) for cs in review.scorecard.scores],
        "approval": _approval_doc(review.approval),
        "decision_history": [_record_doc(r) for r in review.decision_history],
        "graphs": [_graph_doc(g) for g in review.graphs.all()],
        "evidence": [_evidence_doc(e) for e in review.evidence_graph],
        "quality": {
            "coverage": review.quality.coverage.value,
            "grounding": review.quality.grounding.value,
            "confidence": review.quality.confidence.value,
        },
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[CDEvidenceId, ...]:
    return tuple(CDEvidenceId.from_string(i) for i in raw)


def _finding(doc: dict) -> Finding:
    return Finding(
        id=FindingId.from_string(doc["id"]), dimension=ReviewDimension(doc["dimension"]),
        severity=FindingSeverity(doc["severity"]), statement=doc["statement"],
        anti_pattern=(AntiPattern(doc["anti_pattern"]) if doc["anti_pattern"] else None),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _change(doc: dict) -> RequiredChange:
    return RequiredChange(
        id=RequiredChangeId.from_string(doc["id"]), dimension=ReviewDimension(doc["dimension"]),
        description=doc["description"], priority=Priority(doc["priority"]),
        impact=Priority(doc["impact"]), blocking=doc["blocking"],
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _dimension(doc: dict) -> DimensionReview:
    return DimensionReview(
        id=DimensionReviewId.from_string(doc["id"]), dimension=ReviewDimension(doc["dimension"]),
        verdict=Verdict(doc["verdict"]), quality_score=Score(doc["quality_score"]),
        confidence=Confidence(doc["confidence"]), notes=doc["notes"],
        findings=tuple(_finding(f) for f in doc["findings"]),
        required_changes=tuple(_change(c) for c in doc["required_changes"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _profile(doc: dict) -> ReviewProfile:
    return ReviewProfile(
        kind=ReviewProfileKind(doc["kind"]),
        weights={ScoreCategory(c): Weight(w) for c, w in doc["weights"].items()},
        hard_gates={ScoreCategory(c): Score(s) for c, s in doc["hard_gates"].items()},
        default_threshold=Score(doc["default_threshold"]),
    )


def _policy(doc: dict) -> ReviewPolicy:
    return ReviewPolicy(
        profile=_profile(doc["profile"]), mode=ReviewMode(doc["mode"]),
        threshold_override=(Score(doc["threshold_override"]) if doc["threshold_override"] else None),
    )


def _score(doc: dict) -> CategoryScore:
    return CategoryScore(
        category=ScoreCategory(doc["category"]), score=Score(doc["score"]),
        weight=Weight(doc["weight"]),
        dimensions=tuple(ReviewDimension(d) for d in doc["dimensions"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _approval(doc: dict) -> ApprovalDecision:
    return ApprovalDecision(
        id=DecisionId.from_string(doc["id"]), status=ApprovalStatus(doc["status"]),
        rationale=doc["rationale"], decided_by=DeciderRole(doc["decided_by"]),
        decided_at=datetime.fromisoformat(doc["decided_at"]),
        overall_score=Score(doc["overall_score"]),
        failing_gates=tuple(ScoreCategory(g) for g in doc["failing_gates"]),
        blocking_finding_ids=tuple(FindingId.from_string(i) for i in doc["blocking_finding_ids"]),
        superseded_by=(DecisionId.from_string(doc["superseded_by"]) if doc["superseded_by"] else None),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _record(doc: dict) -> DecisionRecord:
    return DecisionRecord(
        decision_id=DecisionId.from_string(doc["decision_id"]),
        status=ApprovalStatus(doc["status"]), decided_by=DeciderRole(doc["decided_by"]),
        decided_at=datetime.fromisoformat(doc["decided_at"]), rationale=doc["rationale"],
        version=doc["version"],
    )


def _graph(doc: dict) -> CDGraph:
    return CDGraph.of(
        GraphKind(doc["kind"]),
        [CDNode(id=CDNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [CDEdge(id=CDEdgeId.from_string(e["id"]), source=CDNodeId.from_string(e["source"]),
                target=CDNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def _evidence(doc: dict) -> CDEvidence:
    return CDEvidence(
        id=CDEvidenceId.from_string(doc["id"]), provenance=ProvenanceKind(doc["provenance"]),
        external_ref=doc["external_ref"], claim=doc["claim"],
        confidence=Confidence(doc["confidence"]), statement=doc.get("statement", ""),
        source_name=doc.get("source_name", ""),
        tags=frozenset(Tag.of(t) for t in doc.get("tags", ())),
    )


def from_document(doc: dict) -> CreativeDirectorReview:
    """Reconstruct a review from its document, re-validating every invariant."""
    dimension_reviews = tuple(_dimension(d) for d in doc["dimension_reviews"])
    scorecard = Scorecard.of(_score(s) for s in doc["scorecard"])
    changes = tuple(c for dr in dimension_reviews for c in dr.required_changes)
    q = doc["quality"]
    return CreativeDirectorReview(
        id=CreativeDirectorReviewId.from_string(doc["id"]),
        lineage_id=CreativeDirectorReviewLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        subject=ReviewSubject(
            kind=SubjectKind(doc["subject"]["kind"]), reference=doc["subject"]["reference"],
            label=doc["subject"]["label"], phase=doc["subject"]["phase"],
        ),
        policy=_policy(doc["policy"]),
        dimension_reviews=dimension_reviews,
        scorecard=scorecard,
        approval=_approval(doc["approval"]),
        decision_history=DecisionHistory.of(_record(r) for r in doc["decision_history"]),
        quality_matrix=QualityMatrix.from_scorecard(scorecard),
        improvement_matrix=ImprovementMatrix.of(changes),
        graphs=CreativeDirectorGraphs.of(_graph(g) for g in doc["graphs"]),
        evidence_graph=EvidenceGraph.of(_evidence(e) for e in doc["evidence"]),
        quality=ReviewQualityMetrics(
            coverage=Percentage(q["coverage"]), grounding=Percentage(q["grounding"]),
            confidence=Confidence(q["confidence"]),
        ),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
