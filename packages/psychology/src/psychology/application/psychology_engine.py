"""The PsychologyEngine — the orchestrator of the psychology pipeline.

Given a request, it runs the full pipeline in fixed order — assemble inputs →
consolidate evidence → synthesise the draft (through the psychologist port) → validate
grounding → build the matrices → apply the frameworks → build the graphs → score →
assemble — producing a single, provenance-tracked, immutable, versioned
:class:`CustomerPsychologyReport`.

It NEVER generates UI, wireframes, or Figma; it produces *structured customer psychology
intelligence* only. The pipeline is deterministic apart from the input and synthesis
ports. Because the report validates provenance integrity at construction, an ungrounded
determination cannot be produced. Every collaborator is injected, so the engine is
framework-independent and testable with fakes.

The synthesis steps of the design (state, personas, drivers, friction, journeys,
objections) are proposed together by the :class:`PsychologySynthesisPort` and disposed of
by the deterministic builders below — *the port proposes, the domain disposes*.
"""

from __future__ import annotations

from psychology.application.commands import BuildPsychology
from psychology.application.pipeline.draft_validator import DraftValidator
from psychology.application.pipeline.evidence_consolidator import EvidenceConsolidator
from psychology.application.pipeline.framework_applier import FrameworkApplier
from psychology.application.pipeline.graph_builder import GraphBuilder
from psychology.application.pipeline.input_assembler import InputAssembler
from psychology.application.pipeline.matrix_builder import MatrixBuilder
from psychology.application.pipeline.quality_scorer import QualityScorer
from psychology.application.ports.brand_input import BrandInputPort
from psychology.application.ports.business_strategy_input import (
    BusinessStrategyInputPort,
)
from psychology.application.ports.clock import Clock
from psychology.application.ports.competitor_insight import CompetitorInsightPort
from psychology.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from psychology.application.ports.reasoning import ReasoningPort
from psychology.application.ports.research_input import ResearchInputPort
from psychology.application.ports.synthesis import PsychologySynthesisPort
from psychology.application.ports.unit_of_work import UnitOfWorkFactory
from psychology.domain.report.report import CustomerPsychologyReport
from psychology.domain.shared.ids import (
    PsychologyReportId,
    PsychologyReportLineageId,
)

__all__ = ["PsychologyEngine"]


class PsychologyEngine:
    """Runs the psychology pipeline and persists a customer psychology report."""

    def __init__(
        self,
        *,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        synthesis: PsychologySynthesisPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        matrix_builder: MatrixBuilder | None = None,
        framework_applier: FrameworkApplier | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
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
        self._matrices = matrix_builder or MatrixBuilder()
        self._frameworks = framework_applier or FrameworkApplier()
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildPsychology) -> CustomerPsychologyReport:
        """Run the full pipeline and persist the resulting report."""
        now = self._clock.now()

        # 1. Assemble inputs from every signal port.
        psychology_input = await self._input.assemble(
            command.request,
            brand=self._brand,
            business_strategy=self._business_strategy,
            knowledge=self._knowledge,
            research=self._research,
            competitor=self._competitor,
            reasoning=self._reasoning,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(psychology_input.signals)

        # 3–8. Synthesise the psychology content, then validate its grounding.
        draft = await self._synthesis.draft(psychology_input, evidence)
        self._draft_validator.validate(draft, evidence)

        # 9–11. Build matrices, apply frameworks, build graphs.
        matrices = self._matrices.build(draft)
        frameworks = self._frameworks.apply(draft, matrices)
        graphs = self._graphs.build(draft.profile, matrices)

        # 12. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(draft, matrices, frameworks)
        report = CustomerPsychologyReport(
            id=PsychologyReportId.new(),
            lineage_id=command.lineage_id or PsychologyReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=command.request.project_id,
            profile=draft.profile,
            personas=draft.personas,
            buying_personas=draft.buying_personas,
            jobs=draft.jobs,
            buying_journey=draft.buying_journey,
            decision_journey=draft.decision_journey,
            matrices=matrices,
            frameworks=frameworks,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    async def _next_version(
        self, lineage_id: PsychologyReportLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1
