"""Stage — Graph construction.

Builds the two orchestrator graphs:

* **EXECUTION** — the deterministic replay script. A single ``SETUP_THEME`` → ``SETUP_TOKENS``
  prologue, then, page by page in order, a ``BUILD_PAGE`` followed by each section's
  ``PLACE_SECTION`` → ``INSTANTIATE_COMPONENT`` → ``APPLY_VARIANT`` → ``APPLY_RESPONSIVE`` →
  ``APPLY_ACCESSIBILITY`` steps, and finally the ``REVIEW_GATE`` steps in review order. Steps are
  chained with ``PRECEDES`` into one total order; every ``INSTANTIATE_COMPONENT`` also
  ``DEPENDS_ON`` the token setup. Each section step carries its section's evidence, so any step
  traces back to its provenance.
* **LAYOUT** — the region containment graph (parent ``CONTAINS`` child).

Both graphs are acyclic by construction; the execution graph's topological order is the sequence
a future Figma phase follows.
"""

from __future__ import annotations

from design_orchestrator.application.contracts import ExecutionDraft
from design_orchestrator.domain.graph.do_graph import DOEdge, DOGraph, DONode
from design_orchestrator.domain.graph.graphs import OrchestratorGraphs
from design_orchestrator.domain.layout.layout import LayoutModel
from design_orchestrator.domain.review.review_plan import ReviewPlan
from design_orchestrator.domain.shared.ids import DOEdgeId, DONodeId
from design_orchestrator.domain.shared.value_objects import (
    ExecutionStepKind,
    GraphKind,
    GraphRelation,
    NodeKind,
)

__all__ = ["GraphBuilder"]

_K = ExecutionStepKind


def _node(kind: NodeKind, label: str, evidence_ids=()) -> DONode:
    return DONode(id=DONodeId.new(), kind=kind, label=label[:120], evidence_ids=tuple(evidence_ids))


def _edge(source: DONodeId, target: DONodeId, relation: GraphRelation) -> DOEdge:
    return DOEdge(id=DOEdgeId.new(), source=source, target=target, relation=relation)


class GraphBuilder:
    """Builds the execution and layout graphs from the resolved plan."""

    def build(
        self, draft: ExecutionDraft, layout_model: LayoutModel, review_plan: ReviewPlan
    ) -> OrchestratorGraphs:
        return OrchestratorGraphs(
            execution=self._execution_graph(draft, review_plan),
            layout=self._layout_graph(layout_model),
        )

    def _execution_graph(self, draft: ExecutionDraft, review_plan: ReviewPlan) -> DOGraph:
        nodes: list[DONode] = []
        edges: list[DOEdge] = []

        theme = _node(NodeKind.STEP, f"{_K.SETUP_THEME.value}")
        tokens = _node(NodeKind.STEP, f"{_K.SETUP_TOKENS.value}")
        nodes.extend((theme, tokens))
        edges.append(_edge(theme.id, tokens.id, GraphRelation.PRECEDES))
        previous = tokens

        for page in draft.pages:
            build_page = _node(NodeKind.PAGE, f"{_K.BUILD_PAGE.value}:{page.page_type.value}")
            nodes.append(build_page)
            edges.append(_edge(previous.id, build_page.id, GraphRelation.PRECEDES))
            previous = build_page
            for section in page.sections:
                ev = section.evidence_ids
                for kind in (
                    _K.PLACE_SECTION,
                    _K.INSTANTIATE_COMPONENT,
                    _K.APPLY_VARIANT,
                    _K.APPLY_RESPONSIVE,
                    _K.APPLY_ACCESSIBILITY,
                ):
                    node_kind = (
                        NodeKind.COMPONENT
                        if kind is _K.INSTANTIATE_COMPONENT
                        else NodeKind.SECTION
                    )
                    step = _node(
                        node_kind,
                        f"{kind.value}:{section.component.value}:{int(section.order)}",
                        ev,
                    )
                    nodes.append(step)
                    edges.append(_edge(previous.id, step.id, GraphRelation.PRECEDES))
                    if kind is _K.INSTANTIATE_COMPONENT:
                        edges.append(_edge(tokens.id, step.id, GraphRelation.DEPENDS_ON))
                    previous = step

        for checkpoint in review_plan:
            gate = _node(NodeKind.STEP, f"{_K.REVIEW_GATE.value}:{checkpoint.gate.value}",
                         checkpoint.evidence_ids)
            nodes.append(gate)
            edges.append(_edge(previous.id, gate.id, GraphRelation.PRECEDES))
            previous = gate

        return DOGraph.of(GraphKind.EXECUTION, nodes, edges)

    def _layout_graph(self, layout_model: LayoutModel) -> DOGraph:
        nodes: dict = {}
        for region in layout_model.regions.values():
            nodes[region.id] = _node(NodeKind.REGION, region.label or region.kind.value)
        edges: list[DOEdge] = []
        for region in layout_model.regions.values():
            if region.parent_id is not None and region.parent_id in nodes:
                edges.append(
                    _edge(nodes[region.parent_id].id, nodes[region.id].id, GraphRelation.CONTAINS)
                )
        return DOGraph.of(GraphKind.LAYOUT, nodes.values(), edges)
