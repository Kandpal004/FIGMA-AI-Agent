"""The Design Language facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, a
future Design System phase, or tests. It runs the design, retrieves specifications, projects
them into views and the neutral design-system bundle, and explains a graph node — returning
serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from design_language.application.commands import BuildDesignLanguage
from design_language.application.design_language_engine import DesignLanguageEngine
from design_language.application.ports.unit_of_work import UnitOfWorkFactory
from design_language.domain.report.bundle import DesignSystemBundle
from design_language.domain.shared.ids import (
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
    DLNodeId,
)
from design_language.domain.shared.value_objects import GraphKind
from design_language.interfaces.dto import (
    DesignSystemBundleView,
    GraphView,
    SpecificationView,
    TraceView,
)

__all__ = ["DesignLanguageFacade"]


class DesignLanguageFacade:
    """Design, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: DesignLanguageEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def design(self, command: BuildDesignLanguage) -> SpecificationView:
        """Run the full pipeline and return the produced specification view."""
        specification = await self._engine.build(command)
        return SpecificationView.from_specification(specification)

    async def get(self, spec_id: DesignLanguageSpecId) -> SpecificationView:
        return SpecificationView.from_specification(await self._load(spec_id))

    async def latest(self, lineage_id: DesignLanguageSpecLineageId) -> SpecificationView:
        async with self._uow() as uow:
            specification = await uow.specifications.latest(lineage_id)
        return SpecificationView.from_specification(specification)

    async def history(
        self, lineage_id: DesignLanguageSpecLineageId
    ) -> list[SpecificationView]:
        async with self._uow() as uow:
            specifications = await uow.specifications.history(lineage_id)
        return [SpecificationView.from_specification(s) for s in specifications]

    # -- projections ------------------------------------------------------- #
    async def visual_dna(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).visual_dna

    async def tokens(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).tokens

    async def grid(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).grid_system

    async def responsive(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).responsive_strategy

    async def philosophies(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).philosophies

    async def personalities(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).personalities

    async def language_selection(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).language_selection

    async def consistency_rules(self, spec_id: DesignLanguageSpecId) -> list[dict]:
        return (await self.get(spec_id)).consistency_rules

    async def composition_rules(self, spec_id: DesignLanguageSpecId) -> list[dict]:
        return (await self.get(spec_id)).composition_rules

    async def constraints(self, spec_id: DesignLanguageSpecId) -> list[dict]:
        return (await self.get(spec_id)).constraints

    async def explanation(self, spec_id: DesignLanguageSpecId) -> dict:
        return (await self.get(spec_id)).explanation

    async def graph(self, spec_id: DesignLanguageSpecId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(spec_id)).graphs[kind.value])

    async def design_system_bundle(
        self, spec_id: DesignLanguageSpecId
    ) -> DesignSystemBundleView:
        """Project a specification into the neutral bundle a Design System phase consumes."""
        specification = await self._load(spec_id)
        return DesignSystemBundleView.from_bundle(
            DesignSystemBundle.from_specification(specification), specification
        )

    async def explain(
        self, spec_id: DesignLanguageSpecId, graph_kind: GraphKind, node_id: DLNodeId
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
    async def _load(self, spec_id: DesignLanguageSpecId):
        async with self._uow() as uow:
            return await uow.specifications.get(spec_id)
