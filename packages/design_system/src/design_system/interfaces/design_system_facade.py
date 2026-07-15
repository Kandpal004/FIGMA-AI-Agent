"""The Design System facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, a future
UI / Figma phase, or tests. It runs the build, retrieves specifications, projects them into views
and the neutral design-system bundle, answers "which tokens / components / themes / constraints",
and explains a graph node — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from design_system.application.commands import BuildDesignSystem
from design_system.application.design_system_engine import DesignSystemEngine
from design_system.application.ports.unit_of_work import UnitOfWorkFactory
from design_system.domain.report.bundle import DesignSystemBundle
from design_system.domain.shared.ids import (
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
    DSNodeId,
)
from design_system.domain.shared.value_objects import ComponentType, GraphKind, ThemeMode
from design_system.interfaces.dto import (
    ComponentView,
    DesignSystemBundleView,
    GraphView,
    SpecificationView,
    TraceView,
)

__all__ = ["DesignSystemFacade"]


class DesignSystemFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: DesignSystemEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def build(self, command: BuildDesignSystem) -> SpecificationView:
        """Run the full pipeline and return the produced specification view."""
        specification = await self._engine.build(command)
        return SpecificationView.from_specification(specification)

    async def get(self, spec_id: DesignSystemSpecId) -> SpecificationView:
        return SpecificationView.from_specification(await self._load(spec_id))

    async def latest(self, lineage_id: DesignSystemSpecLineageId) -> SpecificationView:
        async with self._uow() as uow:
            specification = await uow.specifications.latest(lineage_id)
        return SpecificationView.from_specification(specification)

    async def history(
        self, lineage_id: DesignSystemSpecLineageId
    ) -> list[SpecificationView]:
        async with self._uow() as uow:
            specifications = await uow.specifications.history(lineage_id)
        return [SpecificationView.from_specification(s) for s in specifications]

    # -- projections ------------------------------------------------------- #
    async def tokens(self, spec_id: DesignSystemSpecId) -> list[dict]:
        return (await self.get(spec_id)).tokens

    async def component(
        self, spec_id: DesignSystemSpecId, component: ComponentType
    ) -> ComponentView:
        view = await self.get(spec_id)
        for spec in view.components:
            if spec["component"] == component.value:
                return ComponentView(component=spec)
        raise NotFoundError(
            f"Component {component.value} not found in specification {spec_id}.",
            details={"component": component.value},
        )

    async def components(self, spec_id: DesignSystemSpecId) -> list[dict]:
        return (await self.get(spec_id)).components

    async def themes(self, spec_id: DesignSystemSpecId) -> list[dict]:
        return (await self.get(spec_id)).themes

    async def theme(self, spec_id: DesignSystemSpecId, mode: ThemeMode) -> dict:
        for theme in (await self.get(spec_id)).themes:
            if theme["mode"] == mode.value:
                return theme
        raise NotFoundError(
            f"No {mode.value} theme in specification {spec_id}.",
            details={"mode": mode.value},
        )

    async def constraints(self, spec_id: DesignSystemSpecId) -> list[dict]:
        return (await self.get(spec_id)).constraints

    async def localization(self, spec_id: DesignSystemSpecId) -> dict:
        return (await self.get(spec_id)).localization

    async def platform_mapping(
        self, spec_id: DesignSystemSpecId, component: ComponentType, platform: str
    ) -> dict:
        """The developer/Shopify/Magento mapping for a component."""
        spec = (await self.component(spec_id, component)).component
        mapping = spec["mappings"].get(platform)
        if mapping is None:
            raise NotFoundError(
                f"No {platform} mapping for {component.value} in {spec_id}.",
                details={"platform": platform, "component": component.value},
            )
        return mapping

    async def graph(self, spec_id: DesignSystemSpecId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(spec_id)).graphs[kind.value])

    async def design_system_bundle(
        self, spec_id: DesignSystemSpecId
    ) -> DesignSystemBundleView:
        """Project a specification into the neutral bundle a UI/Figma phase consumes."""
        specification = await self._load(spec_id)
        return DesignSystemBundleView.from_bundle(
            DesignSystemBundle.from_specification(specification), specification
        )

    async def explain(
        self, spec_id: DesignSystemSpecId, graph_kind: GraphKind, node_id: DSNodeId
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
                "id": str(e.id),
                "provenance": e.provenance.value,
                "external_ref": e.external_ref,
                "claim": e.claim,
                "confidence": e.confidence.value,
                "source_name": e.source_name,
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
    async def _load(self, spec_id: DesignSystemSpecId):
        async with self._uow() as uow:
            return await uow.specifications.get(spec_id)
