"""Stage — Graph construction.

Builds the five Figma graphs from the resolved draft:

* **FIGMA_TREE** — every node across pages linked to its children by ``CONTAINS``.
* **COMPONENT** — component sets ``VARIANT_OF`` their variants, and instances ``INSTANCE_OF`` their
  set.
* **AUTO_LAYOUT** — each auto-layout frame linked to the children it lays out (``CONTAINS``).
* **VARIABLE** — collections ``CONTAINS`` their variables, and variables ``ALIASES`` the variables
  they reference.
* **STYLE** — nodes ``USES_STYLE`` styles, and styles ``BINDS`` their backing variables.

Every graph node carries the evidence of the element it represents, so any node, component, or
variable traces back to its provenance — and every upstream engine that grounded the file surfaces
in some node's evidence. Each graph is self-contained (its edges reference only its own nodes) and
acyclic by construction.
"""

from __future__ import annotations

from figma_design.application.contracts import FigmaDraft
from figma_design.domain.graph.fd_graph import FDEdge, FDGraph, FDNode
from figma_design.domain.graph.graphs import FigmaGraphs
from figma_design.domain.shared.ids import FDEdgeId, FDNodeId
from figma_design.domain.shared.value_objects import (
    GraphKind,
    GraphRelation,
    NodeKind,
    NodeType,
)

__all__ = ["GraphBuilder"]


def _node(kind: NodeKind, label: str, evidence_ids=()) -> FDNode:
    return FDNode(id=FDNodeId.new(), kind=kind, label=label[:120], evidence_ids=tuple(evidence_ids))


def _edge(source: FDNodeId, target: FDNodeId, relation: GraphRelation) -> FDEdge:
    return FDEdge(id=FDEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the five Figma graphs from the resolved draft."""

    def build(self, draft: FigmaDraft) -> FigmaGraphs:
        return FigmaGraphs(
            figma_tree=self._figma_tree_graph(draft),
            component=self._component_graph(draft),
            auto_layout=self._auto_layout_graph(draft),
            variable=self._variable_graph(draft),
            style=self._style_graph(draft),
        )

    def _figma_tree_graph(self, draft: FigmaDraft) -> FDGraph:
        nodes: dict = {}
        edges: list[FDEdge] = []
        for page in draft.pages:
            for node in page.tree:
                nodes[node.id] = _node(NodeKind.NODE, node.name, node.evidence_ids)
            for node in page.tree:
                if node.parent_id is not None and node.parent_id in nodes:
                    edges.append(
                        _edge(nodes[node.parent_id].id, nodes[node.id].id, GraphRelation.CONTAINS)
                    )
        return FDGraph.of(GraphKind.FIGMA_TREE, nodes.values(), edges)

    def _component_graph(self, draft: FigmaDraft) -> FDGraph:
        nodes: list[FDNode] = []
        edges: list[FDEdge] = []
        set_nodes: dict = {}
        for component_set in draft.component_sets:
            set_node = _node(
                NodeKind.COMPONENT_SET, component_set.name, component_set.evidence_ids
            )
            set_nodes[component_set.key] = set_node
            nodes.append(set_node)
            for component in component_set.components:
                variant_node = _node(
                    NodeKind.COMPONENT, f"{component_set.key}:{component.name}",
                    component_set.evidence_ids,
                )
                nodes.append(variant_node)
                edges.append(_edge(set_node.id, variant_node.id, GraphRelation.VARIANT_OF))
        for page in draft.pages:
            for node in page.tree.by_type(NodeType.INSTANCE):
                ref = node.instance_ref
                component_set = draft.component_sets.by_id(ref.component_set_id)
                if component_set is None:
                    continue
                inst_node = _node(NodeKind.INSTANCE, node.name, node.evidence_ids)
                nodes.append(inst_node)
                edges.append(
                    _edge(inst_node.id, set_nodes[component_set.key].id, GraphRelation.INSTANCE_OF)
                )
        return FDGraph.of(GraphKind.COMPONENT, nodes, edges)

    def _auto_layout_graph(self, draft: FigmaDraft) -> FDGraph:
        nodes: dict = {}
        edges: list[FDEdge] = []
        for page in draft.pages:
            frames = [n for n in page.tree if n.auto_layout is not None]
            for frame in frames:
                if frame.id not in nodes:
                    nodes[frame.id] = _node(NodeKind.FRAME, frame.name, frame.evidence_ids)
                for child in page.tree.children(frame.id):
                    if child.id not in nodes:
                        nodes[child.id] = _node(NodeKind.NODE, child.name, child.evidence_ids)
                    edges.append(
                        _edge(nodes[frame.id].id, nodes[child.id].id, GraphRelation.CONTAINS)
                    )
        if not nodes:
            nodes_placeholder = _node(NodeKind.FRAME, "no-auto-layout")
            return FDGraph.of(GraphKind.AUTO_LAYOUT, [nodes_placeholder])
        return FDGraph.of(GraphKind.AUTO_LAYOUT, nodes.values(), edges)

    def _variable_graph(self, draft: FigmaDraft) -> FDGraph:
        graph_nodes: list[FDNode] = []
        var_nodes: dict = {}
        edges: list[FDEdge] = []
        for collection in draft.collections:
            col_node = _node(NodeKind.COLLECTION, collection.name)
            graph_nodes.append(col_node)
            for variable in collection:
                var_node = _node(NodeKind.VARIABLE, variable.key)
                var_nodes[variable.key] = var_node
                graph_nodes.append(var_node)
                edges.append(_edge(col_node.id, var_node.id, GraphRelation.CONTAINS))
        for collection in draft.collections:
            for variable in collection:
                for ref in variable.alias_refs:
                    target = var_nodes.get(ref)
                    if target is not None:
                        edges.append(
                            _edge(var_nodes[variable.key].id, target.id, GraphRelation.ALIASES)
                        )
        return FDGraph.of(GraphKind.VARIABLE, graph_nodes, edges)

    def _style_graph(self, draft: FigmaDraft) -> FDGraph:
        nodes: list[FDNode] = []
        edges: list[FDEdge] = []
        style_nodes: dict = {}
        var_nodes: dict = {}
        for style in draft.style_set:
            style_node = _node(NodeKind.STYLE, style.name)
            style_nodes[style.id] = style_node
            nodes.append(style_node)
            for token in style.token_keys:
                if token not in var_nodes:
                    var_nodes[token] = _node(NodeKind.VARIABLE, token)
                    nodes.append(var_nodes[token])
                edges.append(_edge(style_node.id, var_nodes[token].id, GraphRelation.BINDS))
        for page in draft.pages:
            for node in page.tree:
                for ref in (node.fill_style_ref, node.effect_style_ref):
                    if ref is not None and ref in style_nodes:
                        use_node = _node(NodeKind.NODE, node.name, node.evidence_ids)
                        nodes.append(use_node)
                        edges.append(
                            _edge(use_node.id, style_nodes[ref].id, GraphRelation.USES_STYLE)
                        )
        if not nodes:
            return FDGraph.of(GraphKind.STYLE, [_node(NodeKind.STYLE, "no-styles")])
        return FDGraph.of(GraphKind.STYLE, nodes, edges)
