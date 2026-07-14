"""The Intelligence facade — the inbound entry point of the engine.

The single surface everything above the engine calls: the Reasoning/Director layer
(which consults competitive intelligence before design), an API, or tests. It runs
the engine, retrieves reports, and explains recommendations by resolving their
evidence — returning serializable views, never domain aggregates.
"""

from __future__ import annotations

from collections.abc import Sequence

from core.errors import NotFoundError

from competitive.application.commands import AnalyzeCompetitors
from competitive.application.intelligence_engine import IntelligenceEngine
from competitive.application.ports.unit_of_work import UnitOfWorkFactory
from competitive.domain.shared.ids import RecommendationId, ReportId, ReportLineageId
from competitive.interfaces.dto import (
    EvidenceTraceView,
    EvidenceView,
    GapView,
    PatternView,
    RecommendationView,
    ReportView,
    RiskView,
    SwotItemView,
)

__all__ = ["IntelligenceFacade"]


class IntelligenceFacade:
    """Analyse, retrieve, and explain — commands in, views out."""

    def __init__(
        self, engine: IntelligenceEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def analyze(self, command: AnalyzeCompetitors) -> ReportView:
        """Run the full pipeline and return the produced report view."""
        report = await self._engine.analyze(command)
        return ReportView.from_report(report)

    async def get(self, report_id: ReportId) -> ReportView:
        """Retrieve a produced report.

        Raises:
            NotFoundError: If no such report exists.
        """
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        return ReportView.from_report(report)

    async def history(self, lineage_id: ReportLineageId) -> list[ReportView]:
        """Every version of a report lineage, oldest first."""
        async with self._uow() as uow:
            reports = await uow.reports.history(lineage_id)
        return [ReportView.from_report(r) for r in reports]

    async def recommendations(self, report_id: ReportId) -> list[RecommendationView]:
        return (await self.get(report_id)).recommendations

    async def gaps(self, report_id: ReportId) -> list[GapView]:
        return (await self.get(report_id)).gaps

    async def swot(self, report_id: ReportId) -> list[SwotItemView]:
        return (await self.get(report_id)).swot

    async def patterns(self, report_id: ReportId) -> list[PatternView]:
        return (await self.get(report_id)).all_patterns

    async def risks(self, report_id: ReportId) -> list[RiskView]:
        return (await self.get(report_id)).risks

    async def explain(
        self, report_id: ReportId, recommendation_id: RecommendationId
    ) -> EvidenceTraceView:
        """Explain one recommendation by resolving its cited evidence."""
        async with self._uow() as uow:
            report = await uow.reports.get(report_id)
        recommendation = next(
            (r for r in report.recommendations.recommendations if r.id == recommendation_id),
            None,
        )
        if recommendation is None:
            raise NotFoundError(
                f"Recommendation {recommendation_id} not found in report {report_id}.",
                details={"recommendation_id": str(recommendation_id)},
            )
        evidence = [
            EvidenceView.from_ref(report.evidence_graph.get(eid))
            for eid in recommendation.evidence_ids
        ]
        return EvidenceTraceView(
            recommendation=RecommendationView.from_recommendation(recommendation),
            evidence=evidence,
        )
