"""Stage — Graph construction.

Builds the five UX graphs from the draft, wiring the strategy's elements into traversable,
auditable structures: the UX Decision graph (pages derive from the primary goal), the
Navigation graph (pages linked in the storefront order), the Content Hierarchy (each page
contains its prioritised content), the Trust Hierarchy (trust signals under the trust
root), and the Interaction graph (interaction patterns in sequence). Every node carries the
evidence of the element it represents.
"""

from __future__ import annotations

from ux.application.contracts import UXDraft
from ux.domain.graph.graphs import UXGraphs
from ux.domain.graph.ux_graph import UXEdge, UXGraph, UXNode
from ux.domain.shared.ids import UXEdgeId, UXNodeId
from ux.domain.shared.value_objects import (
    GraphKind,
    GraphRelation,
    NodeKind,
    PageKind,
)

__all__ = ["GraphBuilder"]

# A sensible storefront navigation order (edges added only when both pages exist).
_NAV_LINKS: tuple[tuple[PageKind, PageKind], ...] = (
    (PageKind.HOME, PageKind.CATEGORY),
    (PageKind.HOME, PageKind.SEARCH),
    (PageKind.CATEGORY, PageKind.PRODUCT),
    (PageKind.SEARCH, PageKind.PRODUCT),
    (PageKind.PRODUCT, PageKind.CART),
    (PageKind.CART, PageKind.CHECKOUT),
    (PageKind.CHECKOUT, PageKind.POST_PURCHASE),
)


def _node(kind: NodeKind, label: str, evidence_ids=()) -> UXNode:
    return UXNode(id=UXNodeId.new(), kind=kind, label=(label or kind.value)[:120],
                  evidence_ids=tuple(evidence_ids))


def _edge(source: UXNodeId, target: UXNodeId, relation: GraphRelation) -> UXEdge:
    return UXEdge(id=UXEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the five UX graphs from a validated draft."""

    def build(self, draft: UXDraft) -> UXGraphs:
        return UXGraphs(
            decision=self._decision(draft),
            navigation=self._navigation(draft),
            content_hierarchy=self._content_hierarchy(draft),
            trust_hierarchy=self._trust_hierarchy(draft),
            interaction=self._interaction(draft),
        )

    def _decision(self, draft: UXDraft) -> UXGraph:
        nodes: list[UXNode] = []
        edges: list[UXEdge] = []
        primary = draft.goals.primary_user_goal
        root = _node(
            NodeKind.DECISION,
            f"Serve: {primary.statement}" if primary else "Serve the primary user goal",
            primary.evidence_ids if primary else (),
        )
        nodes.append(root)
        for page in draft.pages:
            n = _node(NodeKind.DECISION, page.objective.statement, page.all_evidence_ids())
            nodes.append(n)
            edges.append(_edge(n.id, root.id, GraphRelation.DERIVES_FROM))
        return UXGraph.of(GraphKind.DECISION, nodes, edges)

    def _navigation(self, draft: UXDraft) -> UXGraph:
        page_nodes: dict[PageKind, UXNode] = {}
        nodes: list[UXNode] = []
        for page in draft.pages:
            n = _node(NodeKind.PAGE, page.page.value, page.evidence_ids)
            page_nodes[page.page] = n
            nodes.append(n)
        edges: list[UXEdge] = []
        for source, target in _NAV_LINKS:
            if source in page_nodes and target in page_nodes:
                edges.append(
                    _edge(page_nodes[source].id, page_nodes[target].id, GraphRelation.LINKS_TO)
                )
        return UXGraph.of(GraphKind.NAVIGATION, nodes, edges)

    def _content_hierarchy(self, draft: UXDraft) -> UXGraph:
        nodes: list[UXNode] = []
        edges: list[UXEdge] = []
        for page in draft.pages:
            page_node = _node(NodeKind.PAGE, page.page.value, page.evidence_ids)
            nodes.append(page_node)
            for item in page.content_priority.items:
                c = _node(NodeKind.CONTENT, item.content_type.value, page.content_priority.evidence_ids)
                nodes.append(c)
                edges.append(_edge(page_node.id, c.id, GraphRelation.CONTAINS))
        return UXGraph.of(GraphKind.CONTENT_HIERARCHY, nodes, edges)

    def _trust_hierarchy(self, draft: UXDraft) -> UXGraph:
        trust = draft.strategies.trust
        root = _node(NodeKind.TRUST_ELEMENT, "Trust", trust.evidence_ids)
        nodes: list[UXNode] = [root]
        edges: list[UXEdge] = []
        for signal in (*trust.signals, *trust.trust_moments):
            n = _node(NodeKind.TRUST_ELEMENT, signal, trust.evidence_ids)
            nodes.append(n)
            edges.append(_edge(root.id, n.id, GraphRelation.CONTAINS))
        return UXGraph.of(GraphKind.TRUST_HIERARCHY, nodes, edges)

    def _interaction(self, draft: UXDraft) -> UXGraph:
        interaction = draft.strategies.interaction
        nodes: list[UXNode] = [
            _node(NodeKind.INTERACTION, p.value, interaction.evidence_ids)
            for p in interaction.patterns
        ]
        edges: list[UXEdge] = [
            _edge(nodes[i].id, nodes[i + 1].id, GraphRelation.LEADS_TO)
            for i in range(len(nodes) - 1)
        ]
        return UXGraph.of(GraphKind.INTERACTION, nodes, edges)
