"""Stage — Graph construction.

Builds the two design-language graphs from the validated draft, its rules, and its constraints:

* **VISUAL** — the DNA ``EXPRESSES`` its personalities, ``ELABORATES`` into its philosophies,
  ``MATERIALISES`` into its token system, which is ``CONSTRAINS`` -ed by the visual constraints
  (how the language is built, and what bounds it).
* **LANGUAGE** — the selected archetype is ``INFLUENCES`` -d by its influences and ``REJECTS``
  the considered alternatives (why this language, not those).

Every node carries the evidence of the element it represents, so any node — and therefore any
visual decision — can be explained back to its provenance.
"""

from __future__ import annotations

from design_language.application.contracts import LanguageDraft
from design_language.domain.graph.dl_graph import DLEdge, DLGraph, DLNode
from design_language.domain.graph.graphs import DesignLanguageGraphs
from design_language.domain.rules.constraint import ConstraintSet
from design_language.domain.shared.ids import DLEdgeId, DLNodeId
from design_language.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["GraphBuilder"]


def _node(kind: NodeKind, label: str, evidence_ids=()) -> DLNode:
    return DLNode(
        id=DLNodeId.new(), kind=kind, label=(label or kind.value)[:120],
        evidence_ids=tuple(evidence_ids),
    )


def _edge(source: DLNodeId, target: DLNodeId, relation: GraphRelation) -> DLEdge:
    return DLEdge(id=DLEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the visual and language graphs from a draft and its constraints."""

    def build(
        self, draft: LanguageDraft, constraints: ConstraintSet
    ) -> DesignLanguageGraphs:
        return DesignLanguageGraphs.of([
            self._visual(draft, constraints),
            self._language(draft),
        ])

    def _visual(self, draft: LanguageDraft, constraints: ConstraintSet) -> DLGraph:
        nodes: list[DLNode] = []
        edges: list[DLEdge] = []
        dna_ev = draft.visual_dna.all_evidence_ids()
        dna_node = _node(NodeKind.DNA, draft.visual_dna.visual_style.value, dna_ev)
        nodes.append(dna_node)

        for personality in draft.personalities:
            p_node = _node(NodeKind.PERSONALITY, personality.kind.value, personality.evidence_ids)
            nodes.append(p_node)
            edges.append(_edge(dna_node.id, p_node.id, GraphRelation.EXPRESSES))

        for philosophy in draft.philosophies:
            ph_node = _node(NodeKind.PHILOSOPHY, philosophy.kind.value, philosophy.evidence_ids)
            nodes.append(ph_node)
            edges.append(_edge(dna_node.id, ph_node.id, GraphRelation.ELABORATES))

        token_node = _node(NodeKind.TOKEN, "tokens", draft.tokens.all_evidence_ids() or dna_ev)
        nodes.append(token_node)
        edges.append(_edge(dna_node.id, token_node.id, GraphRelation.MATERIALISES))

        for constraint in constraints:
            c_node = _node(NodeKind.CONSTRAINT, constraint.kind.value, constraint.evidence_ids)
            nodes.append(c_node)
            edges.append(_edge(token_node.id, c_node.id, GraphRelation.CONSTRAINS))

        return DLGraph.of(GraphKind.VISUAL, nodes, edges)

    def _language(self, draft: LanguageDraft) -> DLGraph:
        nodes: list[DLNode] = []
        edges: list[DLEdge] = []
        selection = draft.language_selection
        sel_ev = selection.all_evidence_ids()
        archetype_node = _node(NodeKind.ARCHETYPE, selection.archetype.value, sel_ev)
        nodes.append(archetype_node)

        for influence in selection.influences:
            t_node = _node(NodeKind.TRAIT, influence.value, sel_ev)
            nodes.append(t_node)
            edges.append(_edge(archetype_node.id, t_node.id, GraphRelation.INFLUENCES))

        for alternative in selection.considered:
            a_node = _node(NodeKind.ALTERNATIVE, alternative.option, sel_ev)
            nodes.append(a_node)
            edges.append(_edge(archetype_node.id, a_node.id, GraphRelation.REJECTS))

        return DLGraph.of(GraphKind.LANGUAGE, nodes, edges)
