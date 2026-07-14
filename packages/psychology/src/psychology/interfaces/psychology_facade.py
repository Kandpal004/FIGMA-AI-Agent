"""The Psychology facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer,
downstream UX/CRO phases, or tests. It runs the engine, retrieves reports, projects them
into the neutral UX directive bundle, and explains a graph node by resolving its
successors and evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from psychology.application.commands import BuildPsychology
from psychology.application.ports.unit_of_work import UnitOfWorkFactory
from psychology.application.psychology_engine import PsychologyEngine
from psychology.domain.report.bundle import UXDirectiveBundle
from psychology.domain.shared.ids import (
    PsychNodeId,
    PsychologyReportId,
    PsychologyReportLineageId,
)
from psychology.domain.shared.value_objects import GraphKind
from psychology.interfaces.dto import (
    GraphView,
    MatrixView,
    ProfileView,
    PsychologyTraceView,
    ReportView,
    UXDirectiveBundleView,
)

__all__ = ["PsychologyFacade"]


class PsychologyFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: PsychologyEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def build(self, command: BuildPsychology) -> ReportView:
        """Run the full pipeline and return the produced report view."""
        report = await self._engine.build(command)
        return ReportView.from_report(report)

    async def get(self, report_id: PsychologyReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def latest(self, lineage_id: PsychologyReportLineageId) -> ReportView:
        """The highest-version report of a lineage."""
        async with self._uow() as uow:
            report = await uow.reports.latest(lineage_id)
        return ReportView.from_report(report)

    async def history(
        self, lineage_id: PsychologyReportLineageId
    ) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def profile(self, report_id: PsychologyReportId) -> ProfileView:
        return (await self.get(report_id)).profile

    async def matrices(self, report_id: PsychologyReportId) -> MatrixView:
        return MatrixView(matrices=(await self.get(report_id)).matrices)

    async def graph(
        self, report_id: PsychologyReportId, kind: GraphKind
    ) -> GraphView:
        return GraphView(graph=(await self.get(report_id)).graphs[kind.value])

    async def ux_directive_bundle(
        self, report_id: PsychologyReportId
    ) -> UXDirectiveBundleView:
        """Project a report into the neutral brief downstream UX/CRO consumes."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return UXDirectiveBundleView.from_bundle(UXDirectiveBundle.from_report(report))

    async def explain(
        self,
        report_id: PsychologyReportId,
        graph_kind: GraphKind,
        node_id: PsychNodeId,
    ) -> PsychologyTraceView:
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
        return PsychologyTraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )
