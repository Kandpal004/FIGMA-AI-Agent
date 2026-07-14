"""Stage — Graph construction.

Builds the six IA graphs from the validated draft, wiring the architecture's elements into
traversable, auditable structures: the Site Map (page hierarchy via ``CONTAINS``), the
Navigation graph (nav items ``LINKS_TO`` pages), the Page graph (the primary user flow via
``LEADS_TO``), the Section graph (pages ``CONTAINS`` their shared sections), the Relationship
graph (cross-sell/upsell/related links between pages), and the Content Tree (page → section →
content block via ``CONTAINS``). Every node carries the evidence of the element it
represents.
"""

from __future__ import annotations

from ia.application.contracts import IADraft
from ia.domain.graph.graphs import IAGraphs
from ia.domain.graph.ia_graph import IAEdge, IAGraph, IANode
from ia.domain.shared.ids import IAEdgeId, IANodeId
from ia.domain.shared.value_objects import (
    GraphKind,
    GraphRelation,
    NodeKind,
    PageType,
    RelationshipKind,
)

__all__ = ["GraphBuilder"]

# Primary storefront user flow (edges added only when both pages exist).
_FLOW: tuple[tuple[PageType, PageType], ...] = (
    (PageType.HOMEPAGE, PageType.COLLECTION),
    (PageType.HOMEPAGE, PageType.SEARCH),
    (PageType.COLLECTION, PageType.PRODUCT),
    (PageType.SEARCH, PageType.PRODUCT),
    (PageType.PRODUCT, PageType.CART),
    (PageType.CART, PageType.CHECKOUT),
)

# Relationship kind → graph relation.
_REL: dict[RelationshipKind, GraphRelation] = {
    RelationshipKind.CROSS_SELL: GraphRelation.CROSS_SELLS,
    RelationshipKind.UPSELL: GraphRelation.UPSELLS,
    RelationshipKind.RELATED: GraphRelation.RELATES_TO,
    RelationshipKind.RECOMMENDED: GraphRelation.RELATES_TO,
    RelationshipKind.INTERNAL_LINK: GraphRelation.LINKS_TO,
    RelationshipKind.PARENT_CHILD: GraphRelation.CONTAINS,
    RelationshipKind.SEQUENCE: GraphRelation.PRECEDES,
}


def _node(kind: NodeKind, label: str, evidence_ids=()) -> IANode:
    return IANode(id=IANodeId.new(), kind=kind, label=(label or kind.value)[:120],
                  evidence_ids=tuple(evidence_ids))


def _edge(source: IANodeId, target: IANodeId, relation: GraphRelation) -> IAEdge:
    return IAEdge(id=IAEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the six IA graphs from a validated draft."""

    def build(self, draft: IADraft) -> IAGraphs:
        return IAGraphs(
            sitemap=self._sitemap(draft),
            navigation=self._navigation(draft),
            page=self._page(draft),
            section=self._section(draft),
            relationship=self._relationship(draft),
            content_tree=self._content_tree(draft),
        )

    @staticmethod
    def _page_nodes(draft: IADraft) -> dict[PageType, IANode]:
        return {
            p.page_type: _node(NodeKind.PAGE, p.page_type.value, p.evidence_ids)
            for p in draft.sitemap
        }

    def _sitemap(self, draft: IADraft) -> IAGraph:
        page_nodes = self._page_nodes(draft)
        present = set(page_nodes)
        root = PageType.HOMEPAGE if PageType.HOMEPAGE in present else (
            next(iter(present), None)
        )
        edges: list[IAEdge] = []
        for page_type, node in page_nodes.items():
            if page_type is root:
                continue
            parent = self._parent(page_type, present, root)
            if parent is not None and parent in page_nodes and parent is not page_type:
                edges.append(_edge(page_nodes[parent].id, node.id, GraphRelation.CONTAINS))
        return IAGraph.of(GraphKind.SITEMAP, page_nodes.values(), edges)

    @staticmethod
    def _parent(page_type: PageType, present: set[PageType], root: PageType | None) -> PageType | None:
        if page_type is PageType.PRODUCT and PageType.COLLECTION in present:
            return PageType.COLLECTION
        if page_type is PageType.CHECKOUT and PageType.CART in present:
            return PageType.CART
        return root

    def _navigation(self, draft: IADraft) -> IAGraph:
        page_nodes = self._page_nodes(draft)
        nodes: list[IANode] = list(page_nodes.values())
        edges: list[IAEdge] = []
        for item in draft.navigation.all_items():
            item_node = _node(NodeKind.NAV_ITEM, item.label_intent, item.evidence_ids)
            nodes.append(item_node)
            for target in dict.fromkeys(item.targets()):
                if target in page_nodes:
                    edges.append(_edge(item_node.id, page_nodes[target].id, GraphRelation.LINKS_TO))
        return IAGraph.of(GraphKind.NAVIGATION, nodes, edges)

    def _page(self, draft: IADraft) -> IAGraph:
        page_nodes = self._page_nodes(draft)
        edges = [
            _edge(page_nodes[s].id, page_nodes[t].id, GraphRelation.LEADS_TO)
            for s, t in _FLOW
            if s in page_nodes and t in page_nodes
        ]
        return IAGraph.of(GraphKind.PAGE, page_nodes.values(), edges)

    def _section(self, draft: IADraft) -> IAGraph:
        nodes: list[IANode] = []
        edges: list[IAEdge] = []
        section_nodes: dict[str, IANode] = {}
        for page in draft.sitemap:
            page_node = _node(NodeKind.PAGE, page.page_type.value, page.evidence_ids)
            nodes.append(page_node)
            for section in (*page.required_sections, *page.optional_sections):
                key = section.type.value
                if key not in section_nodes:
                    node = _node(NodeKind.SECTION, key, section.evidence_ids)
                    section_nodes[key] = node
                    nodes.append(node)
                edges.append(_edge(page_node.id, section_nodes[key].id, GraphRelation.CONTAINS))
        return IAGraph.of(GraphKind.SECTION, nodes, edges)

    def _relationship(self, draft: IADraft) -> IAGraph:
        page_nodes = self._page_nodes(draft)
        edges: list[IAEdge] = []
        for rel in draft.relationships:
            if rel.source in page_nodes and rel.target in page_nodes and rel.source is not rel.target:
                edges.append(
                    _edge(page_nodes[rel.source].id, page_nodes[rel.target].id, _REL[rel.kind])
                )
        return IAGraph.of(GraphKind.RELATIONSHIP, page_nodes.values(), edges)

    def _content_tree(self, draft: IADraft) -> IAGraph:
        nodes: list[IANode] = []
        edges: list[IAEdge] = []
        for page in draft.sitemap:
            page_node = _node(NodeKind.PAGE, page.page_type.value, page.evidence_ids)
            nodes.append(page_node)
            for section in (*page.required_sections, *page.optional_sections):
                section_node = _node(NodeKind.SECTION, section.type.value, section.evidence_ids)
                nodes.append(section_node)
                edges.append(_edge(page_node.id, section_node.id, GraphRelation.CONTAINS))
                for block in section.content_blocks:
                    block_node = _node(NodeKind.CONTENT_BLOCK, block.label, block.evidence_ids)
                    nodes.append(block_node)
                    edges.append(_edge(section_node.id, block_node.id, GraphRelation.CONTAINS))
        return IAGraph.of(GraphKind.CONTENT_TREE, nodes, edges)
