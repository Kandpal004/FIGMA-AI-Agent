"""The Figma Design facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, a future
Figma / MCP renderer, or tests. It runs the modelling, retrieves models, projects them into views
and the neutral design bundle, answers "which pages / nodes / variables / styles / component
sets", exposes the token and variant mappings, and explains a graph node — returning serializable
views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from figma_design.application.commands import BuildFigmaDesign
from figma_design.application.figma_design_engine import FigmaDesignEngine
from figma_design.application.ports.unit_of_work import UnitOfWorkFactory
from figma_design.domain.report.bundle import FigmaDesignBundle
from figma_design.domain.shared.ids import (
    FDNodeId,
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
    FigmaPageId,
)
from figma_design.domain.shared.value_objects import FigmaPageKind, GraphKind, StyleType
from figma_design.interfaces.dto import (
    FigmaDesignBundleView,
    FigmaModelView,
    GraphView,
    PageView,
    TraceView,
)

__all__ = ["FigmaDesignFacade"]


class FigmaDesignFacade:
    """Model, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: FigmaDesignEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def compose(self, command: BuildFigmaDesign) -> FigmaModelView:
        """Run the full pipeline and return the produced model view."""
        model = await self._engine.build(command)
        return FigmaModelView.from_model(model)

    async def get(self, model_id: FigmaDesignModelId) -> FigmaModelView:
        return FigmaModelView.from_model(await self._load(model_id))

    async def latest(self, lineage_id: FigmaDesignModelLineageId) -> FigmaModelView:
        async with self._uow() as uow:
            model = await uow.models.latest(lineage_id)
        return FigmaModelView.from_model(model)

    async def history(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> list[FigmaModelView]:
        async with self._uow() as uow:
            models = await uow.models.history(lineage_id)
        return [FigmaModelView.from_model(m) for m in models]

    # -- projections ------------------------------------------------------- #
    async def pages(self, model_id: FigmaDesignModelId) -> list[dict]:
        return (await self.get(model_id)).pages

    async def page(self, model_id: FigmaDesignModelId, page_id: FigmaPageId) -> PageView:
        view = await self.get(model_id)
        for page in view.pages:
            if page["id"] == str(page_id):
                return PageView(page=page)
        raise NotFoundError(
            f"Page {page_id} not found in model {model_id}.", details={"page_id": str(page_id)}
        )

    async def pages_of_kind(
        self, model_id: FigmaDesignModelId, kind: FigmaPageKind
    ) -> list[dict]:
        return [p for p in (await self.get(model_id)).pages if p["kind"] == kind.value]

    async def collections(self, model_id: FigmaDesignModelId) -> list[dict]:
        return (await self.get(model_id)).collections

    async def styles(
        self, model_id: FigmaDesignModelId, style_type: StyleType | None = None
    ) -> list[dict]:
        styles = (await self.get(model_id)).styles
        if style_type is None:
            return styles
        return [s for s in styles if s["type"] == style_type.value]

    async def component_sets(self, model_id: FigmaDesignModelId) -> list[dict]:
        return (await self.get(model_id)).component_sets

    async def token_mapping(self, model_id: FigmaDesignModelId) -> dict:
        return (await self.get(model_id)).token_mapping

    async def variant_mapping(self, model_id: FigmaDesignModelId) -> dict:
        return (await self.get(model_id)).variant_mapping

    async def graph(self, model_id: FigmaDesignModelId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(model_id)).graphs[kind.value])

    async def design_bundle(self, model_id: FigmaDesignModelId) -> FigmaDesignBundleView:
        """Project a model into the neutral bundle a Figma/MCP renderer consumes."""
        model = await self._load(model_id)
        return FigmaDesignBundleView.from_bundle(FigmaDesignBundle.from_model(model), model)

    async def explain(
        self, model_id: FigmaDesignModelId, graph_kind: GraphKind, node_id: FDNodeId
    ) -> TraceView:
        """Explain one graph node by resolving its successors and cited evidence."""
        model = await self._load(model_id)
        graph = model.graphs.get(graph_kind)
        if not graph.has(node_id):
            raise NotFoundError(
                f"Node {node_id} not found in the {graph_kind.value} graph of {model_id}.",
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
            if model.evidence_graph.has(eid)
            for e in (model.evidence_graph.get(eid),)
        ]
        return TraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )

    # ------------------------------------------------------------------ #
    async def _load(self, model_id: FigmaDesignModelId):
        async with self._uow() as uow:
            return await uow.models.get(model_id)
