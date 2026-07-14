"""The Strategy facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer,
downstream design phases, or tests. It runs the engine, retrieves reports, projects
them into the neutral design directive bundle, and explains a decision by resolving its
derivation and evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from strategy.application.commands import BuildStrategy
from strategy.application.ports.unit_of_work import UnitOfWorkFactory
from strategy.application.strategy_engine import StrategyEngine
from strategy.domain.report.bundle import DesignDirectiveBundle
from strategy.domain.shared.ids import (
    StrategicDecisionId,
    StrategyReportId,
    StrategyReportLineageId,
)
from strategy.interfaces.dto import (
    DecisionTraceView,
    DecisionView,
    DesignDirectiveBundleView,
    OpportunityView,
    PriorityItemView,
    ReportView,
    RiskView,
)

__all__ = ["StrategyFacade"]


class StrategyFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: StrategyEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def build(self, command: BuildStrategy) -> ReportView:
        """Run the full pipeline and return the produced report view."""
        report = await self._engine.build(command)
        return ReportView.from_report(report)

    async def get(self, report_id: StrategyReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def latest(self, lineage_id: StrategyReportLineageId) -> ReportView:
        """The highest-version report of a lineage."""
        async with self._uow() as uow:
            report = await uow.reports.latest(lineage_id)
        return ReportView.from_report(report)

    async def history(self, lineage_id: StrategyReportLineageId) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def decisions(self, report_id: StrategyReportId) -> list[DecisionView]:
        return (await self.get(report_id)).decisions

    async def priority_matrix(
        self, report_id: StrategyReportId
    ) -> list[PriorityItemView]:
        return (await self.get(report_id)).priority_matrix

    async def risks(self, report_id: StrategyReportId) -> list[RiskView]:
        return (await self.get(report_id)).risks

    async def opportunities(
        self, report_id: StrategyReportId
    ) -> list[OpportunityView]:
        return (await self.get(report_id)).opportunities

    async def directive_bundle(
        self, report_id: StrategyReportId
    ) -> DesignDirectiveBundleView:
        """Project a report into the neutral brief downstream design consumes."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return DesignDirectiveBundleView.from_bundle(
            DesignDirectiveBundle.from_report(report)
        )

    async def explain(
        self, report_id: StrategyReportId, decision_id: StrategicDecisionId
    ) -> DecisionTraceView:
        """Explain one decision by resolving what it derives from and its evidence."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        if not report.decision_graph.has(decision_id):
            raise NotFoundError(
                f"Decision {decision_id} not found in report {report_id}.",
                details={"decision_id": str(decision_id)},
            )
        decision = report.decision_graph.get(decision_id)
        parents = report.decision_graph.derivation_of(decision_id)
        evidence = [
            {
                "id": str(e.id),
                "provenance": e.provenance.value,
                "external_ref": e.external_ref,
                "claim": e.claim,
                "confidence": e.confidence.value,
                "source_name": e.source_name,
            }
            for eid in decision.evidence_ids
            if report.evidence_graph.has(eid)
            for e in (report.evidence_graph.get(eid),)
        ]
        return DecisionTraceView(
            decision=DecisionView.from_decision(decision),
            derives_from=[DecisionView.from_decision(p) for p in parents],
            evidence=evidence,
        )
