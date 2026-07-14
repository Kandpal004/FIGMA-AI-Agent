"""The BrandEngine — the orchestrator of the brand pipeline.

Given a request, it runs the full pipeline in fixed order — assemble inputs →
consolidate evidence → synthesise the draft (through the brand-strategist port) →
validate grounding → build the brand decision graph → derive governance → score →
assemble — producing a single, provenance-tracked, immutable, versioned
:class:`BrandStrategyReport`.

It NEVER generates UI, Figma, tokens, or copy; it defines the *identity* every future
design decision must follow. The pipeline is deterministic apart from the input and
synthesis ports. Because the report validates provenance integrity at construction, an
ungrounded brand decision or a dangling reference cannot be produced. Every collaborator
is injected, so the engine is framework-independent and testable with fakes.

The eight conceptual synthesis steps of the design (classification, identity,
personality, emotional, visual, verbal) are proposed together by the
:class:`BrandSynthesisPort` and disposed of by the deterministic builders below — *the
port proposes, the domain disposes*.
"""

from __future__ import annotations

from brand.application.commands import BuildBrand
from brand.application.pipeline.decision_graph_builder import DecisionGraphBuilder
from brand.application.pipeline.draft_validator import DraftValidator
from brand.application.pipeline.evidence_consolidator import EvidenceConsolidator
from brand.application.pipeline.governance_builder import GovernanceBuilder
from brand.application.pipeline.input_assembler import InputAssembler
from brand.application.pipeline.quality_scorer import QualityScorer
from brand.application.ports.business_strategy_input import BusinessStrategyInputPort
from brand.application.ports.clock import Clock
from brand.application.ports.competitor_insight import CompetitorInsightPort
from brand.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from brand.application.ports.reasoning import ReasoningPort
from brand.application.ports.research_input import ResearchInputPort
from brand.application.ports.synthesis import BrandSynthesisPort
from brand.application.ports.unit_of_work import UnitOfWorkFactory
from brand.domain.report.report import BrandStrategyReport
from brand.domain.shared.ids import BrandReportId, BrandReportLineageId

__all__ = ["BrandEngine"]


class BrandEngine:
    """Runs the brand pipeline and persists a brand strategy report."""

    def __init__(
        self,
        *,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        synthesis: BrandSynthesisPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        decision_graph_builder: DecisionGraphBuilder | None = None,
        governance_builder: GovernanceBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._business_strategy = business_strategy
        self._knowledge = knowledge
        self._research = research
        self._competitor = competitor
        self._reasoning = reasoning
        self._synthesis = synthesis
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._draft_validator = draft_validator or DraftValidator()
        self._decisions = decision_graph_builder or DecisionGraphBuilder()
        self._governance = governance_builder or GovernanceBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildBrand) -> BrandStrategyReport:
        """Run the full pipeline and persist the resulting report."""
        now = self._clock.now()

        # 1. Assemble inputs from every signal port.
        brand_input = await self._input.assemble(
            command.request,
            business_strategy=self._business_strategy,
            knowledge=self._knowledge,
            research=self._research,
            competitor=self._competitor,
            reasoning=self._reasoning,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(brand_input.signals)

        # 3–8. Synthesise the brand content, then validate its grounding.
        draft = await self._synthesis.draft(brand_input, evidence)
        self._draft_validator.validate(draft, evidence)

        # 9–10. Lift into decisions, derive governance.
        decision_graph = self._decisions.build(draft, evidence)
        governance = self._governance.build(draft)

        # 11. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(draft, decision_graph, governance)
        report = BrandStrategyReport(
            id=BrandReportId.new(),
            lineage_id=command.lineage_id or BrandReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=command.request.project_id,
            classification=draft.classification,
            identity=draft.identity,
            character=draft.character,
            emotional=draft.emotional,
            visual=draft.visual,
            verbal=draft.verbal,
            decision_graph=decision_graph,
            governance=governance,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    async def _next_version(self, lineage_id: BrandReportLineageId | None) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1
