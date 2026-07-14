"""The IntelligenceEngine — the orchestrator of competitor intelligence.

Given a brief, it gathers observations (through the data-source port), builds
profiles, classifies competitors, benchmarks them, **grounds** the relevant
dimensions in Knowledge evidence (through the advisor port), and runs the six
analyzers to produce the recurring patterns and the benchmark / gap / SWOT / best
-practice / risk / recommendation matrices — assembling a single, cited, immutable,
versioned :class:`CompetitorIntelligenceReport`.

The pipeline is deterministic and evidence-backed end to end. Grounding is the one
async fan-out (advisor queries); the analyzers are pure, sync functions of their
inputs, in fixed order. Because the report validates evidence integrity at
construction — and recommendations/best-practices/adopt-patterns each require
evidence at *their* construction — an opinion-based recommendation cannot be
produced. The optional Reasoning port only biases priority; it never invents.

Every collaborator is injected, so the engine is framework-independent and testable
with fakes.
"""

from __future__ import annotations

from competitive.application.benchmark_analyzer import BenchmarkAnalyzer
from competitive.application.best_practice_analyzer import BestPracticeAnalyzer
from competitive.application.classifier import Classifier
from competitive.application.commands import AnalyzeCompetitors
from competitive.application.gap_analyzer import GapAnalyzer
from competitive.application.pattern_analyzer import PatternAnalyzer
from competitive.application.ports.clock import Clock
from competitive.application.ports.data_source import CompetitorDataSourcePort
from competitive.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from competitive.application.ports.reasoning import ReasoningPort
from competitive.application.ports.unit_of_work import UnitOfWorkFactory
from competitive.application.profile_builder import ProfileBuilder
from competitive.application.recommendation_builder import RecommendationBuilder
from competitive.application.risk_analyzer import RiskAnalyzer
from competitive.application.swot_analyzer import SwotAnalyzer
from competitive.domain.competitor.profile import CompetitorProfile
from competitive.domain.evidence.evidence import EvidenceGraph, EvidenceRef
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.report.report import CompetitorIntelligenceReport
from competitive.domain.shared.ids import EvidenceId, ReportId, ReportLineageId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
)

__all__ = ["IntelligenceEngine"]


class IntelligenceEngine:
    """Transforms competitor observations into a cited intelligence report."""

    def __init__(
        self,
        *,
        data_source: CompetitorDataSourcePort,
        advisor: KnowledgeAdvisorPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        reasoning: ReasoningPort | None = None,
        classifier: Classifier | None = None,
        profile_builder: ProfileBuilder | None = None,
        benchmark_analyzer: BenchmarkAnalyzer | None = None,
        pattern_analyzer: PatternAnalyzer | None = None,
        gap_analyzer: GapAnalyzer | None = None,
        swot_analyzer: SwotAnalyzer | None = None,
        best_practice_analyzer: BestPracticeAnalyzer | None = None,
        risk_analyzer: RiskAnalyzer | None = None,
        recommendation_builder: RecommendationBuilder | None = None,
    ) -> None:
        self._data_source = data_source
        self._advisor = advisor
        self._uow = unit_of_work_factory
        self._clock = clock
        self._reasoning = reasoning
        self._classifier = classifier or Classifier()
        self._profiles = profile_builder or ProfileBuilder()
        self._benchmark = benchmark_analyzer or BenchmarkAnalyzer()
        self._patterns = pattern_analyzer or PatternAnalyzer()
        self._gaps = gap_analyzer or GapAnalyzer()
        self._swot = swot_analyzer or SwotAnalyzer()
        self._best = best_practice_analyzer or BestPracticeAnalyzer()
        self._risk = risk_analyzer or RiskAnalyzer()
        self._recommendations = recommendation_builder or RecommendationBuilder()

    async def analyze(self, command: AnalyzeCompetitors) -> CompetitorIntelligenceReport:
        """Run the full pipeline and persist the resulting report."""
        brief = command.brief

        observations = await self._data_source.gather(brief)
        profiles = tuple(
            self._profiles.build(competitor, observations)
            for competitor in brief.competitors
        )
        competitors = self._classifier.classify(
            brief.competitors, profiles, market=brief.market
        )

        benchmark = self._benchmark.build(profiles, brief)

        evidence_by_dimension, evidence_refs = await self._ground(profiles, brief)
        digest = await self._digest(brief)
        priority_dimensions = digest.priority_dimensions if digest else ()

        patterns = self._patterns.detect(profiles, competitors, evidence_by_dimension)
        gap_analysis = self._gaps.analyze(benchmark, evidence_by_dimension)
        swot = self._swot.analyze(benchmark, patterns, evidence_by_dimension)
        best_practices = self._best.build(patterns)
        risk_matrix = self._risk.analyze(gap_analysis, competitors, evidence_by_dimension)
        recommendations = self._recommendations.build(
            patterns, gap_analysis, evidence_by_dimension,
            priority_dimensions=priority_dimensions,
        )

        report = CompetitorIntelligenceReport(
            id=ReportId.new(),
            lineage_id=command.lineage_id or ReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            industry=brief.industry,
            market=brief.market,
            country=brief.country,
            business_goals=brief.business_goals,
            competitors=competitors,
            profiles=profiles,
            patterns=patterns,
            benchmark=benchmark,
            swot=swot,
            gap_analysis=gap_analysis,
            best_practices=best_practices,
            risk_matrix=risk_matrix,
            recommendations=recommendations,
            evidence_graph=EvidenceGraph.of(evidence_refs),
            confidence=self._confidence(profiles, evidence_by_dimension),
            created_at=self._clock.now(),
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    # ------------------------------------------------------------------ #
    async def _ground(
        self, profiles: tuple[CompetitorProfile, ...], brief: CompetitiveBrief
    ) -> tuple[dict[CompetitorDimension, tuple[EvidenceRef, ...]], tuple[EvidenceRef, ...]]:
        """Query the advisor for each profiled dimension and pin the returned
        principles as evidence."""
        dimensions: list[CompetitorDimension] = []
        for profile in profiles:
            for assessment in profile.assessments:
                if assessment.dimension not in dimensions:
                    dimensions.append(assessment.dimension)

        evidence_by_dimension: dict[CompetitorDimension, tuple[EvidenceRef, ...]] = {}
        all_refs: list[EvidenceRef] = []
        for dimension in dimensions:
            principles = await self._advisor.advise(
                dimension,
                industry=brief.industry,
                market=brief.market,
                tenant_id=brief.tenant_id,
                limit=2,
            )
            refs = tuple(
                EvidenceRef(
                    id=EvidenceId.new(),
                    knowledge_id=p.knowledge_id,
                    entry_version_id=p.entry_version_id,
                    category=p.category,
                    title=p.title,
                    statement=p.statement,
                    source_name=p.source_name,
                    confidence=p.confidence,
                    relevance=p.relevance or f"grounds {dimension.value}",
                    dimension=dimension,
                )
                for p in principles
            )
            if refs:
                evidence_by_dimension[dimension] = refs
                all_refs.extend(refs)
        return evidence_by_dimension, tuple(all_refs)

    async def _digest(self, brief: CompetitiveBrief):
        if self._reasoning is None:
            return None
        return await self._reasoning.digest(brief)

    async def _next_version(self, lineage_id: ReportLineageId | None) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1

    @staticmethod
    def _confidence(
        profiles: tuple[CompetitorProfile, ...],
        evidence_by_dimension: dict[CompetitorDimension, tuple[EvidenceRef, ...]],
    ) -> Confidence:
        """Overall confidence: mean assessment confidence blended with the fraction
        of profiled dimensions that were grounded in evidence."""
        assessments = [a for p in profiles for a in p.assessments]
        if not assessments:
            return Confidence.of(0.0)
        mean_conf = sum(a.confidence.value for a in assessments) / len(assessments)
        dimensions = {a.dimension for a in assessments}
        grounded = sum(1 for d in dimensions if d in evidence_by_dimension)
        coverage = grounded / len(dimensions) if dimensions else 0.0
        return Confidence.clamp(0.6 * mean_conf + 0.4 * coverage)
