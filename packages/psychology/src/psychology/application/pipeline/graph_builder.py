"""Stage — Graph construction.

Builds the six psychology graphs from the profile and the matrices, wiring the model's
elements into traversable, auditable structures: the Customer Decision graph (triggers
and blockers → the decision), the Emotion graph (triggers → emotions), the Trust graph
(signals → requirements), the Objection graph (resolutions → objections), the Motivation
graph (motivations → Maslow needs), and the Behavior graph (prompts → behaviors). Every
node carries the evidence of the element it represents.
"""

from __future__ import annotations

from psychology.domain.graph.graphs import PsychologyGraphs
from psychology.domain.graph.psych_graph import PsychEdge, PsychGraph, PsychNode
from psychology.domain.matrices.matrices import PsychologyMatrices
from psychology.domain.shared.ids import PsychEdgeId, PsychNodeId
from psychology.domain.shared.value_objects import (
    GraphKind,
    GraphRelation,
    NodeKind,
)
from psychology.domain.state.profile import PsychologicalProfile

__all__ = ["GraphBuilder"]


def _node(kind: NodeKind, label: str, evidence_ids=()) -> PsychNode:
    return PsychNode(id=PsychNodeId.new(), kind=kind, label=label[:120], evidence_ids=tuple(evidence_ids))


def _edge(source: PsychNodeId, target: PsychNodeId, relation: GraphRelation) -> PsychEdge:
    return PsychEdge(id=PsychEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the six psychology graphs from the profile and matrices."""

    def build(
        self, profile: PsychologicalProfile, matrices: PsychologyMatrices
    ) -> PsychologyGraphs:
        return PsychologyGraphs(
            decision=self._decision(profile, matrices),
            emotion=self._pair_graph(
                GraphKind.EMOTION, matrices.emotion,
                lambda c: (NodeKind.TRIGGER, c.trigger, NodeKind.EMOTION, c.emotion.value),
                GraphRelation.TRIGGERS,
            ),
            trust=self._pair_graph(
                GraphKind.TRUST, matrices.trust,
                lambda c: (NodeKind.RESOLUTION, c.signal_needed, NodeKind.TRUST, c.requirement),
                GraphRelation.RESOLVES,
            ),
            objection=self._pair_graph(
                GraphKind.OBJECTION, matrices.objection,
                lambda c: (NodeKind.RESOLUTION, c.resolution_strategy, NodeKind.OBJECTION, c.objection),
                GraphRelation.RESOLVES,
            ),
            motivation=self._pair_graph(
                GraphKind.MOTIVATION, matrices.motivation,
                lambda c: (NodeKind.MOTIVATION, c.motivation, NodeKind.NEED, c.maslow_need.value),
                GraphRelation.LEADS_TO,
                dedupe_target=True,
            ),
            behavior=self._pair_graph(
                GraphKind.BEHAVIOR, matrices.behavior,
                lambda c: (NodeKind.TRIGGER, c.prompt or "prompt", NodeKind.BEHAVIOR, c.target_behavior),
                GraphRelation.TRIGGERS,
            ),
        )

    def _decision(
        self, profile: PsychologicalProfile, matrices: PsychologyMatrices
    ) -> PsychGraph:
        nodes: list[PsychNode] = []
        edges: list[PsychEdge] = []
        outcome = _node(NodeKind.DECISION_FACTOR, "Purchase decision")
        nodes.append(outcome)
        for trigger in profile.decision_triggers:
            n = _node(NodeKind.TRIGGER, trigger.description, trigger.evidence_ids)
            nodes.append(n)
            edges.append(_edge(n.id, outcome.id, GraphRelation.LEADS_TO))
        for risk in matrices.risk.by_severity()[:3]:
            n = _node(NodeKind.BLOCKER, risk.risk, risk.evidence_ids)
            nodes.append(n)
            edges.append(_edge(n.id, outcome.id, GraphRelation.BLOCKS))
        return PsychGraph.of(GraphKind.DECISION, nodes, edges)

    @staticmethod
    def _pair_graph(
        kind: GraphKind, cells, extract, relation: GraphRelation, *, dedupe_target: bool = False
    ) -> PsychGraph:
        nodes: list[PsychNode] = []
        edges: list[PsychEdge] = []
        target_by_label: dict[str, PsychNodeId] = {}
        for cell in cells:
            source_kind, source_label, target_kind, target_label = extract(cell)
            evidence = tuple(cell.evidence_ids)
            source_node = _node(source_kind, source_label, evidence)
            nodes.append(source_node)
            if dedupe_target and target_label in target_by_label:
                target_id = target_by_label[target_label]
            else:
                target_node = _node(target_kind, target_label, evidence)
                nodes.append(target_node)
                target_id = target_node.id
                target_by_label[target_label] = target_id
            edges.append(_edge(source_node.id, target_id, relation))
        return PsychGraph.of(kind, nodes, edges)
