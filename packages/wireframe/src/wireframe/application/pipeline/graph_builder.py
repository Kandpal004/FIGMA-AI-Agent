"""Stage — Graph construction.

Builds the six wireframe-planning graphs from the ordered blueprint and the approval plan,
wiring the plan's elements into traversable, auditable structures:

* **WIREFRAME** — page ``CONTAINS`` section ``CONTAINS`` block (the master tree).
* **SECTION_DEPENDENCY** — section ``DEPENDS_ON`` the sections it is built on.
* **CONTENT** — section ``CONTAINS`` block ``REQUIRES`` the data it needs.
* **COMPONENT** — section ``REQUIRES`` component, component ``COMPOSES`` component.
* **EXECUTION** — section ``ORDERED_BEFORE`` the next section in build order.
* **APPROVAL** — gate ``GATES`` its section and ``DEPENDS_ON`` upstream gates.

Every node carries the evidence of the element it represents, so any node can be explained
back to its provenance.
"""

from __future__ import annotations

from wireframe.domain.approval.approval import ApprovalPlan
from wireframe.domain.graph.graphs import WireframeGraphs
from wireframe.domain.graph.wf_graph import WFEdge, WFGraph, WFNode
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.shared.ids import SectionId, WFEdgeId, WFNodeId
from wireframe.domain.shared.value_objects import (
    ComponentKind,
    DataKind,
    GraphKind,
    GraphRelation,
    NodeKind,
)

__all__ = ["GraphBuilder"]


def _node(kind: NodeKind, label: str, evidence_ids=()) -> WFNode:
    return WFNode(
        id=WFNodeId.new(), kind=kind, label=(label or kind.value)[:120],
        evidence_ids=tuple(evidence_ids),
    )


def _edge(source: WFNodeId, target: WFNodeId, relation: GraphRelation) -> WFEdge:
    return WFEdge(id=WFEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the six wireframe graphs from an ordered blueprint and approval plan."""

    def build(self, blueprint: PlanBlueprint, approval_plan: ApprovalPlan) -> WireframeGraphs:
        return WireframeGraphs.of([
            self._wireframe(blueprint),
            self._section_dependency(blueprint),
            self._content(blueprint),
            self._component(blueprint),
            self._execution(blueprint),
            self._approval(blueprint, approval_plan),
        ])

    # ------------------------------------------------------------------ #
    def _wireframe(self, blueprint: PlanBlueprint) -> WFGraph:
        nodes: list[WFNode] = []
        edges: list[WFEdge] = []
        for page in blueprint.pages:
            page_node = _node(NodeKind.PAGE, page.page_type.value, page.evidence_ids)
            nodes.append(page_node)
            for section in page.sections:
                section_node = _node(NodeKind.SECTION, section.type.value, section.evidence_ids)
                nodes.append(section_node)
                edges.append(_edge(page_node.id, section_node.id, GraphRelation.CONTAINS))
                for block in section.blocks:
                    block_node = _node(NodeKind.BLOCK, block.label, block.evidence_ids)
                    nodes.append(block_node)
                    edges.append(_edge(section_node.id, block_node.id, GraphRelation.CONTAINS))
        return WFGraph.of(GraphKind.WIREFRAME, nodes, edges)

    def _section_dependency(self, blueprint: PlanBlueprint) -> WFGraph:
        section_nodes: dict[SectionId, WFNode] = {
            s.id: _node(NodeKind.SECTION, s.type.value, s.evidence_ids)
            for s in blueprint.sections()
        }
        edges: list[WFEdge] = []
        for section in blueprint.sections():
            for dep in section.dependencies:
                if dep in section_nodes:
                    edges.append(
                        _edge(section_nodes[section.id].id, section_nodes[dep].id,
                              GraphRelation.DEPENDS_ON)
                    )
        return WFGraph.of(GraphKind.SECTION_DEPENDENCY, section_nodes.values(), edges)

    def _content(self, blueprint: PlanBlueprint) -> WFGraph:
        nodes: list[WFNode] = []
        edges: list[WFEdge] = []
        data_nodes: dict[DataKind, WFNode] = {}
        for page in blueprint.pages:
            for section in page.sections:
                section_node = _node(NodeKind.SECTION, section.type.value, section.evidence_ids)
                nodes.append(section_node)
                for block in section.blocks:
                    block_node = _node(NodeKind.BLOCK, block.label, block.evidence_ids)
                    nodes.append(block_node)
                    edges.append(_edge(section_node.id, block_node.id, GraphRelation.CONTAINS))
                    for data_kind in block.data_kinds:
                        data_node = data_nodes.get(data_kind)
                        if data_node is None:
                            # Ground the data node in the evidence of the first block that
                            # needs it, so every content node is auditable.
                            data_node = _node(NodeKind.DATA, data_kind.value, block.evidence_ids)
                            data_nodes[data_kind] = data_node
                            nodes.append(data_node)
                        edges.append(_edge(block_node.id, data_node.id, GraphRelation.REQUIRES))
        return WFGraph.of(GraphKind.CONTENT, nodes, edges)

    def _component(self, blueprint: PlanBlueprint) -> WFGraph:
        nodes: list[WFNode] = []
        edges: list[WFEdge] = []
        component_nodes: dict[ComponentKind, WFNode] = {}

        def component_node(kind: ComponentKind, evidence_ids=()) -> WFNode:
            existing = component_nodes.get(kind)
            if existing is None:
                existing = _node(NodeKind.COMPONENT, kind.value, evidence_ids)
                component_nodes[kind] = existing
                nodes.append(existing)
            return existing

        for section in blueprint.sections():
            section_node = _node(NodeKind.SECTION, section.type.value, section.evidence_ids)
            nodes.append(section_node)
            for req in section.all_components():
                comp_node = component_node(req.component, req.evidence_ids)
                edges.append(_edge(section_node.id, comp_node.id, GraphRelation.REQUIRES))
                for dependency in req.depends_on:
                    dep_node = component_node(dependency)
                    if dep_node.id != comp_node.id:
                        edges.append(_edge(comp_node.id, dep_node.id, GraphRelation.COMPOSES))
        return WFGraph.of(GraphKind.COMPONENT, nodes, edges)

    def _execution(self, blueprint: PlanBlueprint) -> WFGraph:
        ordered = sorted(blueprint.sections(), key=lambda s: s.execution_order)
        section_nodes = [
            _node(NodeKind.SECTION, s.type.value, s.evidence_ids) for s in ordered
        ]
        edges = [
            _edge(section_nodes[i].id, section_nodes[i + 1].id, GraphRelation.ORDERED_BEFORE)
            for i in range(len(section_nodes) - 1)
        ]
        return WFGraph.of(GraphKind.EXECUTION, section_nodes, edges)

    def _approval(self, blueprint: PlanBlueprint, approval_plan: ApprovalPlan) -> WFGraph:
        nodes: list[WFNode] = []
        edges: list[WFEdge] = []
        gate_nodes: dict[str, WFNode] = {}
        section_nodes: dict[SectionId, WFNode] = {}

        for req in approval_plan:
            section = blueprint.get_section(req.target)
            section_node = section_nodes.get(req.target)
            if section_node is None:
                label = section.type.value if section is not None else req.target.value.hex[:8]
                section_node = _node(NodeKind.SECTION, label,
                                     section.evidence_ids if section is not None else ())
                section_nodes[req.target] = section_node
                nodes.append(section_node)
            gate_node = _node(NodeKind.APPROVAL_GATE, req.gate.value, req.evidence_ids)
            gate_nodes[str(req.id)] = gate_node
            nodes.append(gate_node)
            edges.append(_edge(gate_node.id, section_node.id, GraphRelation.GATES))

        for req in approval_plan:
            gate_node = gate_nodes[str(req.id)]
            for dependency in req.depends_on:
                dep_node = gate_nodes.get(str(dependency))
                if dep_node is not None:
                    edges.append(_edge(gate_node.id, dep_node.id, GraphRelation.DEPENDS_ON))
        return WFGraph.of(GraphKind.APPROVAL, nodes, edges)
