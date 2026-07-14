"""The IAEngine — the orchestrator of the information-architecture pipeline.

Given a request, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → synthesise the draft (through the architect port) → validate grounding → build the
six graphs → score → assemble — producing a single, provenance-tracked, immutable, versioned
:class:`IAReport`.

It NEVER generates wireframes, UI, or Figma; it defines *information structure* only. The
pipeline is deterministic apart from the input and synthesis ports. Because the report
validates provenance and structural integrity at construction, an ungrounded or
structurally-broken IA cannot be produced. Every collaborator is injected, so the engine is
framework-independent and testable with fakes.

The synthesis steps of the design (site map, navigation, relationships, discovery) are
proposed together by the :class:`IASynthesisPort` and disposed of by the deterministic
builders below — *the port proposes, the domain disposes*.
"""

from __future__ import annotations

from ia.application.commands import BuildIA
from ia.application.pipeline.draft_validator import DraftValidator
from ia.application.pipeline.evidence_consolidator import EvidenceConsolidator
from ia.application.pipeline.graph_builder import GraphBuilder
from ia.application.pipeline.input_assembler import InputAssembler
from ia.application.pipeline.quality_scorer import QualityScorer
from ia.application.ports.brand_input import BrandInputPort
from ia.application.ports.business_strategy_input import BusinessStrategyInputPort
from ia.application.ports.clock import Clock
from ia.application.ports.competitor_insight import CompetitorInsightPort
from ia.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ia.application.ports.psychology_input import PsychologyInputPort
from ia.application.ports.reasoning import ReasoningPort
from ia.application.ports.research_input import ResearchInputPort
from ia.application.ports.synthesis import IASynthesisPort
from ia.application.ports.unit_of_work import UnitOfWorkFactory
from ia.application.ports.ux_input import UXInputPort
from ia.domain.report.report import IAReport
from ia.domain.shared.ids import IAReportId, IAReportLineageId

__all__ = ["IAEngine"]


class IAEngine:
    """Runs the IA pipeline and persists an information architecture report."""

    def __init__(
        self,
        *,
        ux: UXInputPort,
        psychology: PsychologyInputPort,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        synthesis: IASynthesisPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._ux = ux
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
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildIA) -> IAReport:
        """Run the full pipeline and persist the resulting report."""
        now = self._clock.now()

        # 1. Assemble inputs from every signal port.
        ia_input = await self._input.assemble(
            command.request,
            ux=self._ux,
            psychology=self._psychology,
            brand=self._brand,
            business_strategy=self._business_strategy,
            knowledge=self._knowledge,
            research=self._research,
            competitor=self._competitor,
            reasoning=self._reasoning,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(ia_input.signals)

        # 3–6. Synthesise the IA content, then validate its grounding.
        draft = await self._synthesis.draft(ia_input, evidence)
        self._draft_validator.validate(draft, evidence)

        # 7. Build the six graphs.
        graphs = self._graphs.build(draft)

        # 8. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(draft, graphs)
        report = IAReport(
            id=IAReportId.new(),
            lineage_id=command.lineage_id or IAReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=command.request.project_id,
            sitemap=draft.sitemap,
            navigation=draft.navigation,
            relationships=draft.relationships,
            discovery=draft.discovery,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    async def _next_version(self, lineage_id: IAReportLineageId | None) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1
