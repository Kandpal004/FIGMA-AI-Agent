"""The StrategyEngine — the orchestrator of the strategy pipeline.

Given a request, it runs the full pipeline in fixed order — assemble inputs →
consolidate evidence → synthesise the draft (through the strategist port) → validate
grounding → build the decision graph → build the strategy graph → prioritise → analyse
risks and opportunities → score quality → assemble — producing a single,
provenance-tracked, immutable, versioned :class:`BusinessStrategyReport`.

It NEVER generates UI, Figma, wireframes, or copy; it produces *structured business
decisions* only. The pipeline is deterministic apart from the input and synthesis
ports. Because the report validates provenance integrity at construction, an ungrounded
decision or a dangling reference cannot be produced. Every collaborator is injected, so
the engine is framework-independent and testable with fakes.

The eight conceptual synthesis steps of the design (goal, customer, positioning, value,
messaging, trust, pricing, retention) are proposed together by the
:class:`StrategySynthesisPort` and disposed of by the deterministic builders below —
*the port proposes, the domain disposes*.
"""

from __future__ import annotations

from strategy.application.commands import BuildStrategy
from strategy.application.pipeline.decision_graph_builder import DecisionGraphBuilder
from strategy.application.pipeline.draft_validator import DraftValidator
from strategy.application.pipeline.evidence_consolidator import EvidenceConsolidator
from strategy.application.pipeline.input_assembler import InputAssembler
from strategy.application.pipeline.prioritizer import Prioritizer
from strategy.application.pipeline.quality_scorer import QualityScorer
from strategy.application.pipeline.risk_opportunity_analyzer import (
    RiskOpportunityAnalyzer,
)
from strategy.application.pipeline.strategy_graph_builder import StrategyGraphBuilder
from strategy.application.ports.clock import Clock
from strategy.application.ports.competitor_insight import CompetitorInsightPort
from strategy.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from strategy.application.ports.reasoning import ReasoningPort
from strategy.application.ports.research_input import ResearchInputPort
from strategy.application.ports.synthesis import StrategySynthesisPort
from strategy.application.ports.unit_of_work import UnitOfWorkFactory
from strategy.domain.report.report import BusinessStrategyReport
from strategy.domain.shared.ids import StrategyReportId, StrategyReportLineageId

__all__ = ["StrategyEngine"]


class StrategyEngine:
    """Runs the strategy pipeline and persists a business strategy report."""

    def __init__(
        self,
        *,
        research: ResearchInputPort,
        knowledge: KnowledgeAdvisorPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        synthesis: StrategySynthesisPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        decision_graph_builder: DecisionGraphBuilder | None = None,
        strategy_graph_builder: StrategyGraphBuilder | None = None,
        prioritizer: Prioritizer | None = None,
        analyzer: RiskOpportunityAnalyzer | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._research = research
        self._knowledge = knowledge
        self._competitor = competitor
        self._reasoning = reasoning
        self._synthesis = synthesis
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._draft_validator = draft_validator or DraftValidator()
        self._decisions = decision_graph_builder or DecisionGraphBuilder()
        self._graph = strategy_graph_builder or StrategyGraphBuilder()
        self._prioritizer = prioritizer or Prioritizer()
        self._analyzer = analyzer or RiskOpportunityAnalyzer()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildStrategy) -> BusinessStrategyReport:
        """Run the full pipeline and persist the resulting report."""
        now = self._clock.now()

        # 1. Assemble inputs from every evidence port.
        strategy_input = await self._input.assemble(
            command.request,
            research=self._research,
            knowledge=self._knowledge,
            competitor=self._competitor,
            reasoning=self._reasoning,
        )

        # 2. Consolidate every insight into one cited evidence graph.
        evidence = self._consolidator.consolidate(strategy_input.insights)

        # 3–10. Synthesise the strategy content, then validate its grounding.
        draft = await self._synthesis.draft(strategy_input, evidence)
        self._draft_validator.validate(draft, evidence)

        # 11–14. Lift into decisions, graphs, priorities, risks, opportunities.
        decision_graph = self._decisions.build(draft, evidence)
        strategy_graph = self._graph.build(decision_graph)
        priority_matrix = self._prioritizer.prioritize(decision_graph)
        risk_register, opportunity_register = self._analyzer.analyze(draft, evidence)

        # 15. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(draft, decision_graph)
        report = BusinessStrategyReport(
            id=StrategyReportId.new(),
            lineage_id=command.lineage_id or StrategyReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=command.request.project_id,
            goals=draft.goals,
            customer=draft.customer,
            positioning=draft.positioning,
            value_proposition=draft.value_proposition,
            usp=draft.usp,
            messaging=draft.messaging,
            brand_voice=draft.brand_voice,
            brand_personality=draft.brand_personality,
            trust=draft.trust,
            pricing=draft.pricing,
            retention=draft.retention,
            decision_graph=decision_graph,
            strategy_graph=strategy_graph,
            priority_matrix=priority_matrix,
            risk_register=risk_register,
            opportunity_register=opportunity_register,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    async def _next_version(
        self, lineage_id: StrategyReportLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1
