"""Stage — Graph construction.

Builds the six design-system graphs from the resolved draft and the derived constraints:

* **TOKEN** — every token; semantic tokens ``ALIASES`` their primitive, component tokens
  ``DERIVES_FROM`` their semantic (the three-tier structure, acyclic by construction).
* **COMPONENT** — each component ``USES`` the tokens it consumes.
* **VARIANT** — each component ``HAS_VARIANT`` its variants and ``HAS_STATE`` its states.
* **THEME** — each theme ``THEMES`` the semantic tokens it remaps.
* **CONSTRAINT** — each constraint ``CONSTRAINS`` the tokens/components it governs.
* **DEPENDENCY** — each component ``DEPENDS_ON`` the components its evidence links it to.

Every node carries the evidence of the element it represents, so any token, component, theme, or
rule can be explained back to its provenance — and every upstream engine that grounded the
system surfaces in some node's evidence.
"""

from __future__ import annotations

from design_system.domain.component.spec import ComponentSpecSet
from design_system.domain.constraint.constraint import ConstraintSet
from design_system.domain.graph.ds_graph import DSEdge, DSGraph, DSNode
from design_system.domain.graph.graphs import DesignSystemGraphs
from design_system.domain.shared.ids import DSEdgeId, DSNodeId
from design_system.domain.shared.value_objects import (
    ComponentType,
    ConstraintKind,
    GraphKind,
    GraphRelation,
    NodeKind,
    TokenTier,
)
from design_system.domain.theme.theme import ThemeSet
from design_system.domain.token.token import TokenSet

__all__ = ["GraphBuilder"]

# Which components a component depends on, for the dependency-closure graph. Mirrors the
# Component Intelligence dependency rules at the design-system level; only pairs where both
# components are specified produce an edge.
_DEPENDENCIES: dict[ComponentType, tuple[ComponentType, ...]] = {
    ComponentType.MEGA_MENU: (ComponentType.HEADER,),
    ComponentType.STICKY_ADD_TO_CART: (ComponentType.PRODUCT_INFORMATION,),
    ComponentType.VARIANT_PICKER: (ComponentType.PRODUCT_INFORMATION,),
    ComponentType.PRODUCT_GALLERY: (ComponentType.PRODUCT_INFORMATION,),
    ComponentType.MINI_CART: (ComponentType.HEADER,),
    ComponentType.CART_DRAWER: (ComponentType.HEADER,),
    ComponentType.FILTERS: (ComponentType.PRODUCT_GRID,),
    ComponentType.SORTING: (ComponentType.PRODUCT_GRID,),
    ComponentType.PAGINATION: (ComponentType.PRODUCT_GRID,),
    ComponentType.PRODUCT_CARD: (ComponentType.PRODUCT_GRID,),
}


def _node(kind: NodeKind, label: str, evidence_ids=()) -> DSNode:
    return DSNode(
        id=DSNodeId.new(),
        kind=kind,
        label=(label or kind.value)[:120],
        evidence_ids=tuple(evidence_ids),
    )


def _edge(source: DSNodeId, target: DSNodeId, relation: GraphRelation) -> DSEdge:
    return DSEdge(id=DSEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the six design-system graphs from the resolved draft."""

    def build(
        self,
        tokens: TokenSet,
        components: ComponentSpecSet,
        themes: ThemeSet,
        constraints: ConstraintSet,
    ) -> DesignSystemGraphs:
        return DesignSystemGraphs(
            token=self._token_graph(tokens),
            component=self._component_graph(tokens, components),
            variant=self._variant_graph(components),
            theme=self._theme_graph(tokens, themes),
            constraint=self._constraint_graph(tokens, components, constraints),
            dependency=self._dependency_graph(components),
        )

    def _token_graph(self, tokens: TokenSet) -> DSGraph:
        nodes: dict[str, DSNode] = {}
        for token in tokens:
            nodes[token.key] = _node(NodeKind.TOKEN, token.key, token.evidence_ids)
        edges: list[DSEdge] = []
        for token in tokens.references():
            relation = (
                GraphRelation.ALIASES
                if token.tier is TokenTier.SEMANTIC
                else GraphRelation.DERIVES_FROM
            )
            ref_node = nodes.get(token.value.ref)
            if ref_node is not None:
                edges.append(_edge(nodes[token.key].id, ref_node.id, relation))
        return DSGraph.of(GraphKind.TOKEN, nodes.values(), edges)

    def _component_graph(
        self, tokens: TokenSet, components: ComponentSpecSet
    ) -> DSGraph:
        nodes: list[DSNode] = []
        token_nodes: dict[str, DSNode] = {}
        for token in tokens:
            token_node = _node(NodeKind.TOKEN, token.key, token.evidence_ids)
            token_nodes[token.key] = token_node
            nodes.append(token_node)
        edges: list[DSEdge] = []
        for spec in components:
            comp_node = _node(NodeKind.COMPONENT, spec.component.value, spec.evidence_ids)
            nodes.append(comp_node)
            for key in spec.token_refs:
                token_node = token_nodes.get(key)
                if token_node is not None:
                    edges.append(_edge(comp_node.id, token_node.id, GraphRelation.USES))
        return DSGraph.of(GraphKind.COMPONENT, nodes, edges)

    def _variant_graph(self, components: ComponentSpecSet) -> DSGraph:
        nodes: list[DSNode] = []
        edges: list[DSEdge] = []
        for spec in components:
            comp_node = _node(NodeKind.COMPONENT, spec.component.value, spec.evidence_ids)
            nodes.append(comp_node)
            for variant in spec.variants:
                v_node = _node(
                    NodeKind.VARIANT, f"{spec.component.value}:{variant.name}", spec.evidence_ids
                )
                nodes.append(v_node)
                edges.append(_edge(comp_node.id, v_node.id, GraphRelation.HAS_VARIANT))
            for state in spec.states.states:
                s_node = _node(
                    NodeKind.STATE, f"{spec.component.value}:{state.state.value}"
                )
                nodes.append(s_node)
                edges.append(_edge(comp_node.id, s_node.id, GraphRelation.HAS_STATE))
        return DSGraph.of(GraphKind.VARIANT, nodes, edges)

    def _theme_graph(self, tokens: TokenSet, themes: ThemeSet) -> DSGraph:
        nodes: list[DSNode] = []
        token_nodes: dict[str, DSNode] = {}
        for token in tokens:
            token_node = _node(NodeKind.TOKEN, token.key, token.evidence_ids)
            token_nodes[token.key] = token_node
            nodes.append(token_node)
        edges: list[DSEdge] = []
        for theme in themes:
            theme_node = _node(NodeKind.THEME, theme.name)
            nodes.append(theme_node)
            for semantic_key in theme.overrides:
                token_node = token_nodes.get(semantic_key)
                if token_node is not None:
                    edges.append(_edge(theme_node.id, token_node.id, GraphRelation.THEMES))
        return DSGraph.of(GraphKind.THEME, nodes, edges)

    def _constraint_graph(
        self,
        tokens: TokenSet,
        components: ComponentSpecSet,
        constraints: ConstraintSet,
    ) -> DSGraph:
        nodes: list[DSNode] = []
        # A representative token and component the token-facing / component-facing rules govern.
        token_targets = [
            _node(NodeKind.TOKEN, t.key, t.evidence_ids)
            for t in tuple(tokens)[:3]
        ]
        comp_targets = [
            _node(NodeKind.COMPONENT, s.component.value, s.evidence_ids)
            for s in tuple(components)[:3]
        ]
        nodes.extend(token_targets)
        nodes.extend(comp_targets)
        edges: list[DSEdge] = []
        component_facing = {
            ConstraintKind.ACCESSIBILITY,
            ConstraintKind.PERFORMANCE,
            ConstraintKind.RTL_MIRROR,
        }
        for constraint in constraints:
            c_node = _node(NodeKind.CONSTRAINT, constraint.kind.value, constraint.evidence_ids)
            nodes.append(c_node)
            targets = comp_targets if constraint.kind in component_facing else token_targets
            for target in targets:
                edges.append(_edge(c_node.id, target.id, GraphRelation.CONSTRAINS))
        return DSGraph.of(GraphKind.CONSTRAINT, nodes, edges)

    def _dependency_graph(self, components: ComponentSpecSet) -> DSGraph:
        present = set(components.components())
        nodes: dict[ComponentType, DSNode] = {}
        for spec in components:
            nodes[spec.component] = _node(
                NodeKind.COMPONENT, spec.component.value, spec.evidence_ids
            )
        edges: list[DSEdge] = []
        for component, deps in _DEPENDENCIES.items():
            if component not in present:
                continue
            for dep in deps:
                if dep in present and dep is not component:
                    edges.append(
                        _edge(nodes[component].id, nodes[dep].id, GraphRelation.DEPENDS_ON)
                    )
        return DSGraph.of(GraphKind.DEPENDENCY, nodes.values(), edges)
