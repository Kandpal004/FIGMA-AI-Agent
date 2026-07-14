"""Stage — Graph construction.

Builds the five Creative Director graphs from the reviewed dimensions, the scorecard, and the
decision, wiring the review's elements into traversable, auditable structures:

* **REVIEW** — subject ``REVIEWS`` dimension ``RAISES`` finding (what was inspected and found).
* **DECISION** — findings and failing gates ``INFORM`` the decision (why it was ruled).
* **APPROVAL** — hard gates ``GATE`` the approval node (what had to pass to sign off).
* **QUALITY_MATRIX** — each category ``SCORES`` the overall (the quality picture).
* **IMPROVEMENT_MATRIX** — each required change ``DERIVES_FROM`` its dimension (the fixes).

Every node carries the evidence of the element it represents, so any node — and therefore any
verdict — can be explained back to its provenance.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.domain.decision.approval import ApprovalDecision
from creative_director.domain.finding.finding import RequiredChange
from creative_director.domain.graph.cd_graph import CDEdge, CDGraph, CDNode
from creative_director.domain.graph.graphs import CreativeDirectorGraphs
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.ids import CDEdgeId, CDNodeId
from creative_director.domain.shared.value_objects import (
    GraphKind,
    GraphRelation,
    NodeKind,
    ScoreCategory,
)

__all__ = ["GraphBuilder"]


def _node(kind: NodeKind, label: str, evidence_ids=()) -> CDNode:
    return CDNode(
        id=CDNodeId.new(), kind=kind, label=(label or kind.value)[:120],
        evidence_ids=tuple(evidence_ids),
    )


def _edge(source: CDNodeId, target: CDNodeId, relation: GraphRelation) -> CDEdge:
    return CDEdge(id=CDEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the five review graphs from the reviewed material."""

    def build(
        self,
        subject_label: str,
        dimension_reviews: Sequence[DimensionReview],
        scorecard: Scorecard,
        approval: ApprovalDecision,
        changes: Sequence[RequiredChange],
    ) -> CreativeDirectorGraphs:
        overall_ev = self._overall_evidence(scorecard)
        return CreativeDirectorGraphs.of([
            self._review(subject_label, dimension_reviews, overall_ev),
            self._decision(dimension_reviews, scorecard, approval),
            self._approval(scorecard, approval),
            self._quality_matrix(scorecard, overall_ev),
            self._improvement_matrix(dimension_reviews, changes),
        ])

    @staticmethod
    def _overall_evidence(scorecard: Scorecard):
        overall = scorecard.get(ScoreCategory.OVERALL)
        return overall.evidence_ids if overall is not None else ()

    def _review(self, subject_label, dimension_reviews, overall_ev) -> CDGraph:
        nodes: list[CDNode] = []
        edges: list[CDEdge] = []
        subject_node = _node(NodeKind.SUBJECT, subject_label or "subject", overall_ev)
        nodes.append(subject_node)
        for dr in dimension_reviews:
            dim_node = _node(NodeKind.DIMENSION, dr.dimension.value, dr.evidence_ids)
            nodes.append(dim_node)
            edges.append(_edge(subject_node.id, dim_node.id, GraphRelation.REVIEWS))
            for finding in dr.findings:
                f_node = _node(NodeKind.FINDING, finding.statement, finding.evidence_ids)
                nodes.append(f_node)
                edges.append(_edge(dim_node.id, f_node.id, GraphRelation.RAISES))
        return CDGraph.of(GraphKind.REVIEW, nodes, edges)

    def _decision(self, dimension_reviews, scorecard, approval) -> CDGraph:
        nodes: list[CDNode] = []
        edges: list[CDEdge] = []
        decision_node = _node(NodeKind.DECISION, approval.status.value, approval.evidence_ids)
        nodes.append(decision_node)
        for dr in dimension_reviews:
            for finding in dr.blocking_findings():
                f_node = _node(NodeKind.FINDING, finding.statement, finding.evidence_ids)
                nodes.append(f_node)
                edges.append(_edge(f_node.id, decision_node.id, GraphRelation.INFORMS))
        for category in approval.failing_gates:
            cs = scorecard.get(category)
            gate_node = _node(NodeKind.GATE, category.value,
                              cs.evidence_ids if cs is not None else ())
            nodes.append(gate_node)
            edges.append(_edge(gate_node.id, decision_node.id, GraphRelation.INFORMS))
        return CDGraph.of(GraphKind.DECISION, nodes, edges)

    def _approval(self, scorecard, approval) -> CDGraph:
        nodes: list[CDNode] = []
        edges: list[CDEdge] = []
        approval_node = _node(NodeKind.DECISION, approval.status.value, approval.evidence_ids)
        nodes.append(approval_node)
        for cs in scorecard.substantive():
            gate_node = _node(NodeKind.GATE, cs.category.value, cs.evidence_ids)
            nodes.append(gate_node)
            edges.append(_edge(gate_node.id, approval_node.id, GraphRelation.GATES))
        return CDGraph.of(GraphKind.APPROVAL, nodes, edges)

    def _quality_matrix(self, scorecard, overall_ev) -> CDGraph:
        nodes: list[CDNode] = []
        edges: list[CDEdge] = []
        overall_node = _node(NodeKind.CATEGORY, ScoreCategory.OVERALL.value, overall_ev)
        nodes.append(overall_node)
        for cs in scorecard.substantive():
            cat_node = _node(NodeKind.CATEGORY, f"{cs.category.value}:{cs.score.value:.0f}",
                             cs.evidence_ids)
            nodes.append(cat_node)
            edges.append(_edge(cat_node.id, overall_node.id, GraphRelation.SCORES))
        return CDGraph.of(GraphKind.QUALITY_MATRIX, nodes, edges)

    def _improvement_matrix(self, dimension_reviews, changes) -> CDGraph:
        nodes: list[CDNode] = []
        edges: list[CDEdge] = []
        dim_nodes: dict[str, CDNode] = {}
        for dr in dimension_reviews:
            node = _node(NodeKind.DIMENSION, dr.dimension.value, dr.evidence_ids)
            dim_nodes[dr.dimension.value] = node
            nodes.append(node)
        for change in changes:
            c_node = _node(NodeKind.CHANGE, change.description, change.evidence_ids)
            nodes.append(c_node)
            dim_node = dim_nodes.get(change.dimension.value)
            if dim_node is not None:
                edges.append(_edge(c_node.id, dim_node.id, GraphRelation.DERIVES_FROM))
        return CDGraph.of(GraphKind.IMPROVEMENT_MATRIX, nodes, edges)
