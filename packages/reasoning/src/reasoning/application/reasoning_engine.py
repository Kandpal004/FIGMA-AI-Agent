"""The ReasoningEngine — the orchestrator that thinks before any design.

Given a request, the engine loads the surrounding context through its ports, runs
every :class:`DimensionReasoner` in a fixed order, assembles their contributions
into the reason/decision/evidence graphs and the typed strategy sections, then
derives risk, confidence, trade-offs, and alternatives — and produces a single,
cited, immutable :class:`DesignStrategy`.

The whole pipeline is deterministic: reasoners are pure functions of the context
and the (deterministic) knowledge advisor, run in a fixed order; risk and
confidence are formulas. The only clock use is the strategy's ``created_at``
timestamp. Because the :class:`DesignStrategy` validates evidence/reason integrity
at construction, a strategy that fabricates or dangles a citation cannot be
produced — the anti-hallucination guarantee holds end to end.

Every collaborator is injected (the reasoners, the ports, the analyzers), so the
engine is framework-independent and unit-testable with fakes.
"""

from __future__ import annotations

from collections.abc import Sequence

from reasoning.application.alternative_generator import AlternativeGenerator
from reasoning.application.commands import GenerateStrategy
from reasoning.application.confidence_calculator import ConfidenceCalculator
from reasoning.application.dimensions.base import (
    DimensionReasoner,
    DimensionResult,
    ReasonerToolkit,
    StrategyOutputKey as K,
)
from reasoning.application.ports.clock import Clock
from reasoning.application.ports.context_port import ContextPort
from reasoning.application.ports.decision_history_port import DecisionHistoryPort
from reasoning.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from reasoning.application.ports.unit_of_work import UnitOfWorkFactory
from reasoning.application.risk_analyzer import RiskAnalyzer
from reasoning.application.tradeoff_deriver import TradeoffDeriver
from reasoning.domain.evidence.evidence import EvidenceGraph
from reasoning.domain.graph.decision import DecisionGraph
from reasoning.domain.graph.reason import ReasonGraph
from reasoning.domain.request.request import ReasoningContext
from reasoning.domain.shared.ids import ReasoningRunId, StrategyId
from reasoning.domain.shared.value_objects import ReasoningDimension
from reasoning.domain.strategy.sections import (
    BusinessObjective,
    CompetitiveStrategy,
    ConversionStrategy,
    CustomerProfile,
    ExperienceStrategy,
    PlatformStrategy,
    ReviewStrategy,
    VisualStrategy,
)
from reasoning.domain.strategy.strategy import DesignStrategy
from reasoning.domain.strategy.structure import StructureStrategy

__all__ = ["ReasoningEngine"]


class ReasoningEngine:
    """Transforms intent + context into a cited, deterministic design strategy."""

    def __init__(
        self,
        *,
        reasoners: Sequence[DimensionReasoner],
        advisor: KnowledgeAdvisorPort,
        context_port: ContextPort,
        decision_history_port: DecisionHistoryPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        toolkit: ReasonerToolkit | None = None,
        risk_analyzer: RiskAnalyzer | None = None,
        confidence_calculator: ConfidenceCalculator | None = None,
        tradeoff_deriver: TradeoffDeriver | None = None,
        alternative_generator: AlternativeGenerator | None = None,
    ) -> None:
        self._reasoners = tuple(reasoners)
        self._advisor = advisor
        self._context_port = context_port
        self._history_port = decision_history_port
        self._uow = unit_of_work_factory
        self._clock = clock
        self._toolkit = toolkit or ReasonerToolkit()
        self._risk = risk_analyzer or RiskAnalyzer()
        self._confidence = confidence_calculator or ConfidenceCalculator()
        self._tradeoffs = tradeoff_deriver or TradeoffDeriver()
        self._alternatives = alternative_generator or AlternativeGenerator()

    async def generate(self, command: GenerateStrategy) -> DesignStrategy:
        """Run the full reasoning pipeline and persist the resulting strategy."""
        context = await self._load_context(command)
        merged = await self._run_reasoners(context)

        evidence_graph = EvidenceGraph.of(merged.evidence)
        reason_graph = self._build_reason_graph(context, merged)
        decision_graph = DecisionGraph.of(merged.decisions)

        risk = self._risk.analyze(decision_graph, evidence_graph, merged.gaps)
        confidence = self._confidence.calculate(
            evidence_graph, merged.gaps, context.stance
        )
        tradeoffs = merged.tradeoffs + self._tradeoffs.derive(decision_graph, evidence_graph)
        alternatives = self._alternatives.generate(context.stance, confidence.overall)

        strategy = DesignStrategy(
            id=StrategyId.new(),
            run_id=ReasoningRunId.new(),
            project_id=context.request.project_id,
            section_id=context.request.section_id,
            page_type=context.request.page_type,
            stance=context.stance,
            business=BusinessObjective(
                objective=merged.first(K.BUSINESS_OBJECTIVE),
                secondary=merged.get(K.BUSINESS_SECONDARY),
            ),
            customer=CustomerProfile(
                who=merged.first(K.CUSTOMER_WHO),
                target_market=merged.first(K.TARGET_MARKET),
                problems=merged.get(K.PROBLEMS),
                objections=merged.get(K.OBJECTIONS),
                emotional_triggers=merged.get(K.EMOTIONAL_TRIGGERS),
                trust_mechanisms=merged.get(K.TRUST_MECHANISMS),
            ),
            conversion=ConversionStrategy(principles=merged.get(K.CRO_PRINCIPLES)),
            experience=ExperienceStrategy(
                ux_principles=merged.get(K.UX_PRINCIPLES),
                accessibility_rules=merged.get(K.ACCESSIBILITY_RULES),
            ),
            platform=PlatformStrategy(
                shopify_constraints=merged.get(K.SHOPIFY_CONSTRAINTS),
                magento_constraints=merged.get(K.MAGENTO_CONSTRAINTS),
            ),
            competitive=CompetitiveStrategy(
                competitors_to_research=merged.get(K.COMPETITORS)
            ),
            visual=VisualStrategy(
                design_system=merged.first(K.DESIGN_SYSTEM),
                typography=merged.first(K.TYPOGRAPHY),
                spacing=merged.first(K.SPACING),
                visual_hierarchy=merged.first(K.VISUAL_HIERARCHY),
            ),
            structure=StructureStrategy(sections=merged.sections),
            review=ReviewStrategy(review_points=merged.get(K.REVIEW_POINTS)),
            reason_graph=reason_graph,
            decision_graph=decision_graph,
            evidence_graph=evidence_graph,
            risk_assessment=risk,
            confidence=confidence,
            tradeoffs=tradeoffs,
            alternatives=alternatives,
            gaps=merged.gaps,
            created_at=self._clock.now(),
        )

        async with self._uow() as uow:
            await uow.strategies.save(strategy)
            await uow.commit()
        return strategy

    # ------------------------------------------------------------------ #
    async def _load_context(self, command: GenerateStrategy) -> ReasoningContext:
        request = command.request
        brand = await self._context_port.load_brand(
            request.project_id, tenant_id=command.tenant_id
        )
        facts = await self._context_port.load_memory_facts(
            request.project_id, section_id=request.section_id, tenant_id=command.tenant_id
        )
        priors = await self._history_port.load_prior_decisions(
            request.project_id, section_id=request.section_id, tenant_id=command.tenant_id
        )
        return ReasoningContext.build(
            request,
            brand=brand,
            memory_facts=facts,
            prior_decisions=priors,
            tenant_id=command.tenant_id,
        )

    async def _run_reasoners(self, context: ReasoningContext) -> DimensionResult:
        results: list[DimensionResult] = []
        for reasoner in self._reasoners:
            results.append(await reasoner.reason(context, self._advisor, self._toolkit))
        return DimensionResult.merge(*results)

    def _build_reason_graph(
        self, context: ReasoningContext, merged: DimensionResult
    ) -> ReasonGraph:
        """Add approved prior decisions as premise nodes, then the reasoners'
        reasons (all roots, so order is safe)."""
        graph = ReasonGraph.empty()
        for prior in context.approved_decisions():
            premise = self._toolkit.reason(
                ReasoningDimension.BUSINESS,
                "Prior approved decision (a binding premise)",
                prior.summary,
                confidence=1.0,
            )
            graph = graph.add_node(premise)
        for reason in merged.reasons:
            graph = graph.add_node(reason)
        return graph
