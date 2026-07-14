"""The Research facade — the inbound entry point of the engine.

The single surface everything above the engine calls: the Reasoning/Director layer
(which pulls research evidence before design), an API, or tests. It runs the engine,
retrieves reports, projects them for downstream reasoning, and explains an entity by
resolving its evidence — returning serializable views and the neutral reasoning
bundle, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from research.application.commands import Research
from research.application.ports.unit_of_work import UnitOfWorkFactory
from research.application.research_engine import ResearchEngine
from research.domain.report.bundle import ReasoningBundle
from research.domain.shared.ids import (
    EntityId,
    ResearchReportId,
    ResearchReportLineageId,
)
from research.interfaces.dto import (
    EntityView,
    EvidenceTraceView,
    EvidenceView,
    ReasoningBundleView,
    RelationshipView,
    ReportView,
)

__all__ = ["ResearchFacade"]


class ResearchFacade:
    """Research, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: ResearchEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def research(self, command: Research) -> ReportView:
        """Run the full acquisition pipeline and return the produced report view."""
        report = await self._engine.research(command)
        return ReportView.from_report(report)

    async def get(self, report_id: ResearchReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def latest(self, lineage_id: ResearchReportLineageId) -> ReportView:
        """The highest-version report of a lineage."""
        async with self._uow() as uow:
            report = await uow.reports.latest(lineage_id)
        return ReportView.from_report(report)

    async def history(self, lineage_id: ResearchReportLineageId) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def evidence(self, report_id: ResearchReportId) -> list[EvidenceView]:
        return (await self.get(report_id)).evidence

    async def entities(self, report_id: ResearchReportId) -> list[EntityView]:
        return (await self.get(report_id)).entities

    async def relationships(self, report_id: ResearchReportId) -> list[RelationshipView]:
        return (await self.get(report_id)).relationships

    async def reasoning_bundle(self, report_id: ResearchReportId) -> ReasoningBundleView:
        """Project a report into the neutral bundle downstream reasoning consumes."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReasoningBundleView.from_bundle(ReasoningBundle.from_report(report))

    async def explain(
        self, report_id: ResearchReportId, entity_id: EntityId
    ) -> EvidenceTraceView:
        """Explain one entity by resolving the evidence that supports it."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        if not report.entity_graph.has(entity_id):
            raise NotFoundError(
                f"Entity {entity_id} not found in report {report_id}.",
                details={"entity_id": str(entity_id)},
            )
        entity = report.entity_graph.get(entity_id)
        evidence = [
            EvidenceView.from_evidence(report.evidence_graph.get(eid))
            for eid in entity.evidence_ids
            if report.evidence_graph.has(eid)
        ]
        return EvidenceTraceView(
            entity=EntityView.from_entity(entity), evidence=evidence
        )
