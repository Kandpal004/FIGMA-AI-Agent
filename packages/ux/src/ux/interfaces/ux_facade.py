"""The UX facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer,
downstream wireframe/design phases, or tests. It runs the engine, retrieves reports,
projects them into the neutral design brief bundle, and explains a graph node by resolving
its successors and evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from ux.application.commands import BuildUXStrategy
from ux.application.ports.unit_of_work import UnitOfWorkFactory
from ux.application.ux_engine import UXEngine
from ux.domain.report.bundle import DesignBriefBundle
from ux.domain.shared.ids import UXNodeId, UXReportId, UXReportLineageId
from ux.domain.shared.value_objects import GraphKind, JourneyKind, PageKind
from ux.interfaces.dto import (
    DesignBriefBundleView,
    GraphView,
    PageView,
    ReportView,
    UXTraceView,
)

__all__ = ["UXFacade"]


class UXFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(self, engine: UXEngine, unit_of_work_factory: UnitOfWorkFactory) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def build(self, command: BuildUXStrategy) -> ReportView:
        """Run the full pipeline and return the produced report view."""
        report = await self._engine.build(command)
        return ReportView.from_report(report)

    async def get(self, report_id: UXReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def latest(self, lineage_id: UXReportLineageId) -> ReportView:
        """The highest-version report of a lineage."""
        async with self._uow() as uow:
            report = await uow.reports.latest(lineage_id)
        return ReportView.from_report(report)

    async def history(self, lineage_id: UXReportLineageId) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def pages(self, report_id: UXReportId) -> list[dict]:
        return (await self.get(report_id)).pages

    async def page(self, report_id: UXReportId, page: PageKind) -> PageView:
        for view in (await self.get(report_id)).pages:
            if view["page"] == page.value:
                return PageView(page=view)
        raise NotFoundError(
            f"Page {page.value} not found in report {report_id}.",
            details={"page": page.value},
        )

    async def journey(self, report_id: UXReportId, kind: JourneyKind) -> dict:
        return (await self.get(report_id)).journeys[kind.value]

    async def graph(self, report_id: UXReportId, kind: GraphKind) -> GraphView:
        return GraphView(graph=(await self.get(report_id)).graphs[kind.value])

    async def design_brief_bundle(
        self, report_id: UXReportId
    ) -> DesignBriefBundleView:
        """Project a report into the neutral brief downstream design consumes."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return DesignBriefBundleView.from_bundle(DesignBriefBundle.from_report(report))

    async def explain(
        self, report_id: UXReportId, graph_kind: GraphKind, node_id: UXNodeId
    ) -> UXTraceView:
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
        return UXTraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )
