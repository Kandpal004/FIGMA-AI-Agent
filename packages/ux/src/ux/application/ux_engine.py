"""The UXEngine — the orchestrator of the UX strategy pipeline.

Given a request, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → synthesise the draft (through the UX-strategist port) → validate grounding →
build the friction/drop-off analyses → apply the UX laws → build the graphs → score →
assemble — producing a single, provenance-tracked, immutable, versioned
:class:`UXStrategyReport`.

It NEVER generates wireframes, UI, or Figma; it produces *UX decisions* only. The pipeline
is deterministic apart from the input and synthesis ports. Because the report validates
provenance integrity at construction, an ungrounded UX decision cannot be produced. Every
collaborator is injected, so the engine is framework-independent and testable with fakes.

The synthesis steps of the design (goals, mental model, pages, journeys, flows,
strategies) are proposed together by the :class:`UXSynthesisPort` and disposed of by the
deterministic builders below — *the port proposes, the domain disposes*.
"""

from __future__ import annotations

from ux.application.commands import BuildUXStrategy
from ux.application.pipeline.analysis_builder import AnalysisBuilder
from ux.application.pipeline.draft_validator import DraftValidator
from ux.application.pipeline.evidence_consolidator import EvidenceConsolidator
from ux.application.pipeline.graph_builder import GraphBuilder
from ux.application.pipeline.input_assembler import InputAssembler
from ux.application.pipeline.law_applier import LawApplier
from ux.application.pipeline.quality_scorer import QualityScorer
from ux.application.ports.brand_input import BrandInputPort
from ux.application.ports.business_strategy_input import BusinessStrategyInputPort
from ux.application.ports.clock import Clock
from ux.application.ports.competitor_insight import CompetitorInsightPort
from ux.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ux.application.ports.psychology_input import PsychologyInputPort
from ux.application.ports.reasoning import ReasoningPort
from ux.application.ports.research_input import ResearchInputPort
from ux.application.ports.synthesis import UXSynthesisPort
from ux.application.ports.unit_of_work import UnitOfWorkFactory
from ux.domain.report.report import UXStrategyReport
from ux.domain.shared.ids import UXReportId, UXReportLineageId

__all__ = ["UXEngine"]


class UXEngine:
    """Runs the UX strategy pipeline and persists a UX strategy report."""

    def __init__(
        self,
        *,
        psychology: PsychologyInputPort,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        synthesis: UXSynthesisPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        analysis_builder: AnalysisBuilder | None = None,
        law_applier: LawApplier | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._psychology = psychology
        self._brand = brand
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
        self._analysis = analysis_builder or AnalysisBuilder()
        self._laws = law_applier or LawApplier()
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildUXStrategy) -> UXStrategyReport:
        """Run the full pipeline and persist the resulting report."""
        now = self._clock.now()

        # 1. Assemble inputs from every signal port.
        ux_input = await self._input.assemble(
            command.request,
            psychology=self._psychology,
            brand=self._brand,
            business_strategy=self._business_strategy,
            knowledge=self._knowledge,
            research=self._research,
            competitor=self._competitor,
            reasoning=self._reasoning,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(ux_input.signals)

        # 3–7. Synthesise the UX content, then validate its grounding.
        draft = await self._synthesis.draft(ux_input, evidence)
        self._draft_validator.validate(draft, evidence)

        # 8–10. Build analyses, apply laws, build graphs.
        friction, dropoff = self._analysis.build(draft.journeys)
        laws = self._laws.apply(evidence)
        graphs = self._graphs.build(draft)

        # 11. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(draft, laws, friction, dropoff)
        report = UXStrategyReport(
            id=UXReportId.new(),
            lineage_id=command.lineage_id or UXReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=command.request.project_id,
            goals=draft.goals,
            mental_model=draft.mental_model,
            pages=draft.pages,
            journeys=draft.journeys,
            flows=draft.flows,
            strategies=draft.strategies,
            friction=friction,
            dropoff=dropoff,
            laws=laws,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    async def _next_version(self, lineage_id: UXReportLineageId | None) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1
