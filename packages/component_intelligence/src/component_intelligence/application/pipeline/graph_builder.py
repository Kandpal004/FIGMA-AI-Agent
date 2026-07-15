"""Stage — Graph construction.

Builds the two component graphs from the coherent composition, its compatibility web, and its
placement rules:

* **COMPONENT** — each included component is ``PLACED_ON`` the pages it belongs to (which
  component belongs on which page).
* **DEPENDENCY** — components ``DEPENDS_ON`` / ``REQUIRES`` / ``ENHANCES`` / ``CONFLICTS_WITH``
  one another (the intelligence web behind inclusion).

Every node carries the evidence of the component (or page) it represents, so any inclusion or
placement decision can be explained back to its provenance.
"""

from __future__ import annotations

from component_intelligence.domain.compatibility.compatibility import CompatibilitySet
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.graph.ci_graph import CIEdge, CIGraph, CINode
from component_intelligence.domain.graph.graphs import ComponentGraphs
from component_intelligence.domain.rules.placement_rules import PlacementRuleSet
from component_intelligence.domain.shared.ids import CIEdgeId, CINodeId
from component_intelligence.domain.shared.value_objects import (
    CompatibilityKind,
    ComponentType,
    GraphKind,
    GraphRelation,
    NodeKind,
    PageType,
)

__all__ = ["GraphBuilder"]

_COMPAT_RELATION = {
    CompatibilityKind.REQUIRES: GraphRelation.REQUIRES,
    CompatibilityKind.ENHANCES: GraphRelation.ENHANCES,
    CompatibilityKind.CONFLICTS_WITH: GraphRelation.CONFLICTS_WITH,
    CompatibilityKind.REPLACES: GraphRelation.REPLACES,
}


def _node(kind: NodeKind, label: str, evidence_ids=()) -> CINode:
    return CINode(
        id=CINodeId.new(), kind=kind, label=(label or kind.value)[:120],
        evidence_ids=tuple(evidence_ids),
    )


def _edge(source: CINodeId, target: CINodeId, relation: GraphRelation) -> CIEdge:
    return CIEdge(id=CIEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the component and dependency graphs from a coherent composition."""

    def build(
        self,
        composition: ComponentComposition,
        compatibility: CompatibilitySet,
        placement: PlacementRuleSet,
    ) -> ComponentGraphs:
        return ComponentGraphs.of([
            self._component_graph(composition, placement),
            self._dependency_graph(composition, compatibility),
        ])

    def _component_graph(
        self, composition: ComponentComposition, placement: PlacementRuleSet
    ) -> CIGraph:
        nodes: list[CINode] = []
        edges: list[CIEdge] = []
        component_nodes: dict[ComponentType, CINode] = {}
        for decision in composition.included():
            node = _node(NodeKind.COMPONENT, decision.component.value, decision.all_evidence_ids())
            component_nodes[decision.component] = node
            nodes.append(node)

        page_nodes: dict[PageType, CINode] = {}
        for page in placement.pages():
            page_evidence = tuple(
                eid for rule in placement.for_page(page) for eid in rule.evidence_ids
            )
            page_node = _node(NodeKind.PAGE, page.value, page_evidence)
            page_nodes[page] = page_node
            nodes.append(page_node)

        for rule in placement:
            component_node = component_nodes.get(rule.component)
            page_node = page_nodes.get(rule.page)
            if component_node is not None and page_node is not None:
                edges.append(_edge(component_node.id, page_node.id, GraphRelation.PLACED_ON))
        return CIGraph.of(GraphKind.COMPONENT, nodes, edges)

    def _dependency_graph(
        self, composition: ComponentComposition, compatibility: CompatibilitySet
    ) -> CIGraph:
        included = composition.included_components()
        nodes: list[CINode] = []
        component_nodes: dict[ComponentType, CINode] = {}
        for decision in composition.included():
            node = _node(NodeKind.COMPONENT, decision.component.value, decision.all_evidence_ids())
            component_nodes[decision.component] = node
            nodes.append(node)

        edges: list[CIEdge] = []
        for decision in composition.included():
            for dep in decision.dependencies:
                if dep in included and dep is not decision.component:
                    edges.append(_edge(
                        component_nodes[decision.component].id, component_nodes[dep].id,
                        GraphRelation.DEPENDS_ON,
                    ))
        for link in compatibility:
            if (
                link.source in included and link.target in included
                and link.source is not link.target
            ):
                edges.append(_edge(
                    component_nodes[link.source].id, component_nodes[link.target].id,
                    _COMPAT_RELATION[link.kind],
                ))
        return CIGraph.of(GraphKind.DEPENDENCY, nodes, edges)
