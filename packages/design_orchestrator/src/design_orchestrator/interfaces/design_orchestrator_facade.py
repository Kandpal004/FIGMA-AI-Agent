"""The Design Orchestrator facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, a future
Figma / MCP generation phase, or tests. It runs the orchestration, retrieves plans, projects them
into views and the neutral execution bundle, answers "which sections on which page / in which
order", exposes the token and variant mappings and the review gates, and explains a graph node —
returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from design_orchestrator.application.commands import BuildExecutionPlan
from design_orchestrator.application.design_orchestrator_engine import DesignOrchestratorEngine
from design_orchestrator.application.ports.unit_of_work import UnitOfWorkFactory
from design_orchestrator.domain.report.bundle import ExecutionPlanBundle
from design_orchestrator.domain.shared.ids import (
    DesignExecutionPlanId,
    DesignExecutionPlanLineageId,
    DONodeId,
)
from design_orchestrator.domain.shared.value_objects import GraphKind, PageType
from design_orchestrator.interfaces.dto import (
    ExecutionPlanBundleView,
    ExecutionPlanView,
    GraphView,
    PageView,
    TraceView,
)

__all__ = ["DesignOrchestratorFacade"]


class DesignOrchestratorFacade:
    """Orchestrate, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: DesignOrchestratorEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def orchestrate(self, command: BuildExecutionPlan) -> ExecutionPlanView:
        """Run the full pipeline and return the produced plan view."""
        plan = await self._engine.build(command)
        return ExecutionPlanView.from_plan(plan)

    async def get(self, plan_id: DesignExecutionPlanId) -> ExecutionPlanView:
        return ExecutionPlanView.from_plan(await self._load(plan_id))

    async def latest(self, lineage_id: DesignExecutionPlanLineageId) -> ExecutionPlanView:
        async with self._uow() as uow:
            plan = await uow.plans.latest(lineage_id)
        return ExecutionPlanView.from_plan(plan)

    async def history(
        self, lineage_id: DesignExecutionPlanLineageId
    ) -> list[ExecutionPlanView]:
        async with self._uow() as uow:
            plans = await uow.plans.history(lineage_id)
        return [ExecutionPlanView.from_plan(p) for p in plans]

    # -- projections ------------------------------------------------------- #
    async def page(self, plan_id: DesignExecutionPlanId, page_type: PageType) -> PageView:
        view = await self.get(plan_id)
        for page in view.pages:
            if page["page_type"] == page_type.value:
                return PageView(page=page)
        raise NotFoundError(
            f"Page {page_type.value} not found in plan {plan_id}.",
            details={"page_type": page_type.value},
        )

    async def pages(self, plan_id: DesignExecutionPlanId) -> list[dict]:
        return (await self.get(plan_id)).pages

    async def execution_order(self, plan_id: DesignExecutionPlanId) -> list[dict]:
        return (await self.get(plan_id)).execution_order

    async def component_tree(self, plan_id: DesignExecutionPlanId) -> list[dict]:
        return (await self.get(plan_id)).component_tree

    async def layout(self, plan_id: DesignExecutionPlanId) -> dict:
        return (await self.get(plan_id)).layout

    async def token_mapping(self, plan_id: DesignExecutionPlanId) -> dict:
        return (await self.get(plan_id)).token_mapping

    async def variant_mapping(self, plan_id: DesignExecutionPlanId) -> dict:
        return (await self.get(plan_id)).variant_mapping

    async def review_plan(self, plan_id: DesignExecutionPlanId) -> list[dict]:
        return (await self.get(plan_id)).review_plan

    async def graph(self, plan_id: DesignExecutionPlanId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(plan_id)).graphs[kind.value])

    async def execution_bundle(
        self, plan_id: DesignExecutionPlanId
    ) -> ExecutionPlanBundleView:
        """Project a plan into the neutral bundle a Figma/MCP phase consumes."""
        plan = await self._load(plan_id)
        return ExecutionPlanBundleView.from_bundle(
            ExecutionPlanBundle.from_plan(plan), plan
        )

    async def explain(
        self, plan_id: DesignExecutionPlanId, graph_kind: GraphKind, node_id: DONodeId
    ) -> TraceView:
        """Explain one graph node by resolving its successors and cited evidence."""
        plan = await self._load(plan_id)
        graph = plan.graphs.get(graph_kind)
        if not graph.has(node_id):
            raise NotFoundError(
                f"Node {node_id} not found in the {graph_kind.value} graph of {plan_id}.",
                details={"node_id": str(node_id)},
            )
        node = graph.get(node_id)
        successors = graph.successors(node_id)
        evidence = [
            {
                "id": str(e.id),
                "provenance": e.provenance.value,
                "external_ref": e.external_ref,
                "claim": e.claim,
                "confidence": e.confidence.value,
                "source_name": e.source_name,
            }
            for eid in node.evidence_ids
            if plan.evidence_graph.has(eid)
            for e in (plan.evidence_graph.get(eid),)
        ]
        return TraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )

    # ------------------------------------------------------------------ #
    async def _load(self, plan_id: DesignExecutionPlanId):
        async with self._uow() as uow:
            return await uow.plans.get(plan_id)
