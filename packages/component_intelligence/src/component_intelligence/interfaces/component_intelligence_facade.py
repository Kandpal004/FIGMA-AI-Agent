"""The Component Intelligence facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, a future
Design System phase, or tests. It runs the composition, retrieves specifications, projects them
into views and the neutral component bundle, answers "which components on which page" and "why
this component", and explains a graph node — returning serializable views, never domain
aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from component_intelligence.application.commands import BuildComposition
from component_intelligence.application.component_intelligence_engine import (
    ComponentIntelligenceEngine,
)
from component_intelligence.application.ports.unit_of_work import UnitOfWorkFactory
from component_intelligence.domain.report.bundle import ComponentSpecBundle
from component_intelligence.domain.shared.ids import (
    CINodeId,
    ComponentSpecId,
    ComponentSpecLineageId,
)
from component_intelligence.domain.shared.value_objects import ComponentType, GraphKind, PageType
from component_intelligence.interfaces.dto import (
    ComponentSpecBundleView,
    ComponentView,
    GraphView,
    SpecificationView,
    TraceView,
)

__all__ = ["ComponentIntelligenceFacade"]


class ComponentIntelligenceFacade:
    """Compose, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: ComponentIntelligenceEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def compose(self, command: BuildComposition) -> SpecificationView:
        """Run the full pipeline and return the produced specification view."""
        specification = await self._engine.build(command)
        return SpecificationView.from_specification(specification)

    async def get(self, spec_id: ComponentSpecId) -> SpecificationView:
        return SpecificationView.from_specification(await self._load(spec_id))

    async def latest(self, lineage_id: ComponentSpecLineageId) -> SpecificationView:
        async with self._uow() as uow:
            specification = await uow.specifications.latest(lineage_id)
        return SpecificationView.from_specification(specification)

    async def history(self, lineage_id: ComponentSpecLineageId) -> list[SpecificationView]:
        async with self._uow() as uow:
            specifications = await uow.specifications.history(lineage_id)
        return [SpecificationView.from_specification(s) for s in specifications]

    # -- projections ------------------------------------------------------- #
    async def component(
        self, spec_id: ComponentSpecId, component: ComponentType
    ) -> ComponentView:
        view = await self.get(spec_id)
        for decision in view.components:
            if decision["component"] == component.value:
                return ComponentView(component=decision)
        raise NotFoundError(
            f"Component {component.value} not found in specification {spec_id}.",
            details={"component": component.value},
        )

    async def composition(self, spec_id: ComponentSpecId) -> list[dict]:
        view = await self.get(spec_id)
        return [d for d in view.components if d["inclusion"] == "included"]

    async def page_components(self, spec_id: ComponentSpecId, page: PageType) -> list[dict]:
        """Which components belong on a page, in placement order."""
        view = await self.get(spec_id)
        rules = [r for r in view.placement_rules if r["page"] == page.value]
        rules.sort(key=lambda r: (r["region"], r["order"]))
        return rules

    async def placement_rules(self, spec_id: ComponentSpecId) -> list[dict]:
        return (await self.get(spec_id)).placement_rules

    async def visibility_rules(self, spec_id: ComponentSpecId) -> list[dict]:
        return (await self.get(spec_id)).visibility_rules

    async def responsive_rules(self, spec_id: ComponentSpecId) -> list[dict]:
        return (await self.get(spec_id)).responsive_rules

    async def reuse_rules(self, spec_id: ComponentSpecId) -> list[dict]:
        return (await self.get(spec_id)).reuse_rules

    async def composition_rules(self, spec_id: ComponentSpecId) -> list[dict]:
        return (await self.get(spec_id)).composition_rules

    async def compatibility(self, spec_id: ComponentSpecId) -> dict:
        return (await self.get(spec_id)).compatibility

    async def conflicts(self, spec_id: ComponentSpecId) -> list[dict]:
        return (await self.get(spec_id)).compatibility["conflicts"]

    async def why(self, spec_id: ComponentSpecId, component: ComponentType) -> dict:
        """The WHY / WHEN / WHEN-NOT intelligence for a component."""
        decision = (await self.component(spec_id, component)).component
        return {
            "component": decision["component"], "inclusion": decision["inclusion"],
            "purposes": decision["purposes"], "impacts": decision["impacts"],
            "when_to_use": decision["usage"]["when_to_use"],
            "when_not_to_use": decision["usage"]["when_not_to_use"],
            "conflicts_with": decision["usage"]["conflicts_with"],
            "considered_alternative": decision["considered_alternative"],
        }

    async def graph(self, spec_id: ComponentSpecId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(spec_id)).graphs[kind.value])

    async def design_system_bundle(
        self, spec_id: ComponentSpecId
    ) -> ComponentSpecBundleView:
        """Project a specification into the neutral bundle a Design System phase consumes."""
        specification = await self._load(spec_id)
        return ComponentSpecBundleView.from_bundle(
            ComponentSpecBundle.from_specification(specification), specification
        )

    async def explain(
        self, spec_id: ComponentSpecId, graph_kind: GraphKind, node_id: CINodeId
    ) -> TraceView:
        """Explain one graph node by resolving its successors and cited evidence."""
        specification = await self._load(spec_id)
        graph = specification.graphs.get(graph_kind)
        if not graph.has(node_id):
            raise NotFoundError(
                f"Node {node_id} not found in the {graph_kind.value} graph of {spec_id}.",
                details={"node_id": str(node_id)},
            )
        node = graph.get(node_id)
        successors = graph.successors(node_id)
        evidence = [
            {
                "id": str(e.id), "provenance": e.provenance.value,
                "external_ref": e.external_ref, "claim": e.claim,
                "confidence": e.confidence.value, "source_name": e.source_name,
            }
            for eid in node.evidence_ids
            if specification.evidence_graph.has(eid)
            for e in (specification.evidence_graph.get(eid),)
        ]
        return TraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )

    # ------------------------------------------------------------------ #
    async def _load(self, spec_id: ComponentSpecId):
        async with self._uow() as uow:
            return await uow.specifications.get(spec_id)
