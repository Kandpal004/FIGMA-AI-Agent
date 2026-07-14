"""The IA facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer,
downstream wireframe phases, or tests. It runs the engine, retrieves reports, projects them
into the neutral wireframe brief bundle, and explains a graph node by resolving its
successors and evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from ia.application.commands import BuildIA
from ia.application.ia_engine import IAEngine
from ia.application.ports.unit_of_work import UnitOfWorkFactory
from ia.domain.report.bundle import WireframeBriefBundle
from ia.domain.shared.ids import IANodeId, IAReportId, IAReportLineageId
from ia.domain.shared.value_objects import GraphKind, PageType
from ia.interfaces.dto import (
    GraphView,
    IATraceView,
    NavigationView,
    PageView,
    ReportView,
    WireframeBriefBundleView,
)

__all__ = ["IAFacade"]


class IAFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(self, engine: IAEngine, unit_of_work_factory: UnitOfWorkFactory) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def build(self, command: BuildIA) -> ReportView:
        """Run the full pipeline and return the produced report view."""
        report = await self._engine.build(command)
        return ReportView.from_report(report)

    async def get(self, report_id: IAReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def latest(self, lineage_id: IAReportLineageId) -> ReportView:
        """The highest-version report of a lineage."""
        async with self._uow() as uow:
            report = await uow.reports.latest(lineage_id)
        return ReportView.from_report(report)

    async def history(self, lineage_id: IAReportLineageId) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def sitemap(self, report_id: IAReportId) -> list[dict]:
        view = await self.get(report_id)
        return [*view.required_pages, *view.optional_pages]

    async def page(self, report_id: IAReportId, page_type: PageType) -> PageView:
        view = await self.get(report_id)
        for page in (*view.required_pages, *view.optional_pages):
            if page["page_type"] == page_type.value:
                return PageView(page=page)
        raise NotFoundError(
            f"Page {page_type.value} not found in report {report_id}.",
            details={"page_type": page_type.value},
        )

    async def navigation(self, report_id: IAReportId) -> NavigationView:
        return NavigationView(navigation=(await self.get(report_id)).navigation)

    async def relationships(self, report_id: IAReportId) -> list[dict]:
        return (await self.get(report_id)).relationships

    async def discovery(self, report_id: IAReportId) -> dict:
        return (await self.get(report_id)).discovery

    async def graph(self, report_id: IAReportId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(report_id)).graphs[kind.value])

    async def wireframe_brief_bundle(
        self, report_id: IAReportId
    ) -> WireframeBriefBundleView:
        """Project a report into the neutral brief downstream wireframing consumes."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return WireframeBriefBundleView.from_bundle(WireframeBriefBundle.from_report(report))

    async def explain(
        self, report_id: IAReportId, graph_kind: GraphKind, node_id: IANodeId
    ) -> IATraceView:
        """Explain one graph node by resolving its successors and cited evidence."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        graph = report.graphs.get(graph_kind)
        if not graph.has(node_id):
            raise NotFoundError(
                f"Node {node_id} not found in the {graph_kind.value} graph of {report_id}.",
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
            if report.evidence_graph.has(eid)
            for e in (report.evidence_graph.get(eid),)
        ]
        return IATraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )
