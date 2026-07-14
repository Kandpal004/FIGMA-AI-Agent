"""The Wireframe facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, a
future Figma design phase, or tests. It runs the engine, retrieves plans, projects them into
views and the neutral Figma plan bundle, and explains a graph node by resolving its
successors and evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from wireframe.application.commands import BuildWireframePlan
from wireframe.application.ports.unit_of_work import UnitOfWorkFactory
from wireframe.application.wireframe_engine import WireframeEngine
from wireframe.domain.report.bundle import FigmaPlanBundle
from wireframe.domain.shared.ids import (
    SectionId,
    WFNodeId,
    WireframePlanId,
    WireframePlanLineageId,
)
from wireframe.domain.shared.value_objects import GraphKind, PageType
from wireframe.interfaces.dto import (
    ApprovalView,
    FigmaPlanBundleView,
    GraphView,
    PageView,
    PlanView,
    SectionView,
    WireframeTraceView,
)

__all__ = ["WireframeFacade"]


class WireframeFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: WireframeEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def plan(self, command: BuildWireframePlan) -> PlanView:
        """Run the full pipeline and return the produced plan view."""
        plan = await self._engine.build(command)
        return PlanView.from_plan(plan)

    async def get(self, plan_id: WireframePlanId) -> PlanView:
        """Retrieve a produced plan.

        Raises:
            NotFoundError: If no such plan exists.
        """
        async with self._uow() as uow:
            plan = await uow.plans.get(plan_id)
        return PlanView.from_plan(plan)

    async def latest(self, lineage_id: WireframePlanLineageId) -> PlanView:
        """The highest-version plan of a lineage."""
        async with self._uow() as uow:
            plan = await uow.plans.latest(lineage_id)
        return PlanView.from_plan(plan)

    async def history(self, lineage_id: WireframePlanLineageId) -> list[PlanView]:
        """Every version of a plan lineage, oldest first."""
        async with self._uow() as uow:
            plans = await uow.plans.history(lineage_id)
        return [PlanView.from_plan(p) for p in plans]

    async def page(self, plan_id: WireframePlanId, page_type: PageType) -> PageView:
        view = await self.get(plan_id)
        for page in view.pages:
            if page["page_type"] == page_type.value:
                return PageView(page=page)
        raise NotFoundError(
            f"Page {page_type.value} not found in plan {plan_id}.",
            details={"page_type": page_type.value},
        )

    async def section(self, plan_id: WireframePlanId, section_id: SectionId) -> SectionView:
        view = await self.get(plan_id)
        for page in view.pages:
            for section in page["sections"]:
                if section["id"] == str(section_id):
                    return SectionView(section=section)
        raise NotFoundError(
            f"Section {section_id} not found in plan {plan_id}.",
            details={"section_id": str(section_id)},
        )

    async def blocks(self, plan_id: WireframePlanId, section_id: SectionId) -> list[dict]:
        return (await self.section(plan_id, section_id)).section["blocks"]

    async def components(self, plan_id: WireframePlanId, section_id: SectionId) -> dict:
        section = (await self.section(plan_id, section_id)).section
        return {
            "required": section["required_components"],
            "optional": section["optional_components"],
        }

    async def execution_order(self, plan_id: WireframePlanId) -> list[dict]:
        """Every section across the plan, in build order."""
        view = await self.get(plan_id)
        sections = [s for page in view.pages for s in page["sections"]]
        sections.sort(key=lambda s: s["execution_order"])
        return [
            {"execution_order": s["execution_order"], "id": s["id"], "type": s["type"],
             "dependencies": s["dependencies"]}
            for s in sections
        ]

    async def approval_plan(self, plan_id: WireframePlanId) -> ApprovalView:
        return ApprovalView(approval=(await self.get(plan_id)).approval_plan)

    async def content_plan(self, plan_id: WireframePlanId) -> dict:
        """The content/data/asset requirements across the plan."""
        view = await self.get(plan_id)
        content: list[dict] = []
        for page in view.pages:
            for section in page["sections"]:
                content.append({
                    "section_id": section["id"], "type": section["type"],
                    "blocks": section["blocks"],
                    "required_data": section["required_data"],
                    "required_assets": section["required_assets"],
                })
        return {"page_count": view.page_count, "content": content}

    async def graph(self, plan_id: WireframePlanId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(plan_id)).graphs[kind.value])

    async def figma_plan_bundle(self, plan_id: WireframePlanId) -> FigmaPlanBundleView:
        """Project a plan into the neutral bundle a downstream Figma engine consumes."""
        async with self._uow() as uow:
            plan = await uow.plans.get(plan_id)
        return FigmaPlanBundleView.from_bundle(FigmaPlanBundle.from_plan(plan))

    async def explain(
        self, plan_id: WireframePlanId, graph_kind: GraphKind, node_id: WFNodeId
    ) -> WireframeTraceView:
        """Explain one graph node by resolving its successors and cited evidence."""
        async with self._uow() as uow:
            plan = await uow.plans.get(plan_id)
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
        return WireframeTraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )
