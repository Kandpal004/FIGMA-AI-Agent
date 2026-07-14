"""The Brand facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer,
downstream design phases, or tests. It runs the engine, retrieves reports, projects them
into the neutral brand-guidelines bundle, and explains a brand decision by resolving its
derivation and evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from core.errors import NotFoundError

from brand.application.brand_engine import BrandEngine
from brand.application.commands import BuildBrand
from brand.application.ports.unit_of_work import UnitOfWorkFactory
from brand.domain.report.bundle import BrandGuidelinesBundle
from brand.domain.shared.ids import (
    BrandDecisionId,
    BrandReportId,
    BrandReportLineageId,
)
from brand.interfaces.dto import (
    BrandDecisionTraceView,
    BrandDecisionView,
    GovernanceRuleView,
    GuidelinesBundleView,
    ReportView,
    ValidationRuleView,
)

__all__ = ["BrandFacade"]


class BrandFacade:
    """Build, retrieve, project, and explain — commands in, views out."""

    def __init__(
        self, engine: BrandEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def build(self, command: BuildBrand) -> ReportView:
        """Run the full pipeline and return the produced report view."""
        report = await self._engine.build(command)
        return ReportView.from_report(report)

    async def get(self, report_id: BrandReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def latest(self, lineage_id: BrandReportLineageId) -> ReportView:
        """The highest-version report of a lineage."""
        async with self._uow() as uow:
            report = await uow.reports.latest(lineage_id)
        return ReportView.from_report(report)

    async def history(self, lineage_id: BrandReportLineageId) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def decisions(self, report_id: BrandReportId) -> list[BrandDecisionView]:
        return (await self.get(report_id)).decisions

    async def consistency_rules(
        self, report_id: BrandReportId
    ) -> list[GovernanceRuleView]:
        return (await self.get(report_id)).consistency_rules

    async def governance_rules(
        self, report_id: BrandReportId
    ) -> list[GovernanceRuleView]:
        return (await self.get(report_id)).governance_rules

    async def validation_rules(
        self, report_id: BrandReportId
    ) -> list[ValidationRuleView]:
        return (await self.get(report_id)).validation_rules

    async def guidelines_bundle(
        self, report_id: BrandReportId
    ) -> GuidelinesBundleView:
        """Project a report into the neutral brief downstream design consumes."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return GuidelinesBundleView.from_bundle(
            BrandGuidelinesBundle.from_report(report)
        )

    async def explain(
        self, report_id: BrandReportId, decision_id: BrandDecisionId
    ) -> BrandDecisionTraceView:
        """Explain one decision by resolving what it derives from, expresses, and cites."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        if not report.decision_graph.has(decision_id):
            raise NotFoundError(
                f"Decision {decision_id} not found in report {report_id}.",
                details={"decision_id": str(decision_id)},
            )
        decision = report.decision_graph.get(decision_id)
        derives = report.decision_graph.derivation_of(decision_id)
        expresses = report.decision_graph.expressed_by(decision_id)
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
        return BrandDecisionTraceView(
            decision=BrandDecisionView.from_decision(decision),
            derives_from=[BrandDecisionView.from_decision(d) for d in derives],
            expresses=[BrandDecisionView.from_decision(d) for d in expresses],
            evidence=evidence,
        )
