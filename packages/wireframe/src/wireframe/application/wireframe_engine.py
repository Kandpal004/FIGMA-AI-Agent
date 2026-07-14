"""The WireframeEngine — the orchestrator of the wireframe-planning pipeline.

Given a request, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → synthesise the draft (through the planner port) → validate grounding → resolve
execution order → wire approvals → build the six graphs → score → assemble — producing a
single, provenance-tracked, immutable, versioned :class:`WireframePlan`.

It NEVER generates UI, Figma, or HTML; it produces a *planning document* only. The pipeline
is deterministic apart from the input and synthesis ports. Because the plan validates
provenance and structural integrity at construction — and the ordering resolver and graph
primitive reject cycles — an ungrounded or structurally-broken plan cannot be produced. Every
collaborator is injected, so the engine is framework-independent and testable with fakes.

The planner *proposes* the structure and the deterministic stages *dispose* of it — the port
proposes, the domain disposes.
"""

from __future__ import annotations

from wireframe.application.commands import BuildWireframePlan
from wireframe.application.pipeline.approval_planner import ApprovalPlanner
from wireframe.application.pipeline.draft_validator import DraftValidator
from wireframe.application.pipeline.evidence_consolidator import EvidenceConsolidator
from wireframe.application.pipeline.graph_builder import GraphBuilder
from wireframe.application.pipeline.input_assembler import InputAssembler
from wireframe.application.pipeline.ordering_resolver import OrderingResolver
from wireframe.application.pipeline.quality_scorer import QualityScorer
from wireframe.application.ports.brand_input import BrandInputPort
from wireframe.application.ports.business_strategy_input import BusinessStrategyInputPort
from wireframe.application.ports.clock import Clock
from wireframe.application.ports.competitor_insight import CompetitorInsightPort
from wireframe.application.ports.ia_input import IAInputPort
from wireframe.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from wireframe.application.ports.psychology_input import PsychologyInputPort
from wireframe.application.ports.reasoning import ReasoningPort
from wireframe.application.ports.research_input import ResearchInputPort
from wireframe.application.ports.synthesis import WireframeSynthesisPort
from wireframe.application.ports.unit_of_work import UnitOfWorkFactory
from wireframe.application.ports.ux_input import UXInputPort
from wireframe.domain.report.report import WireframePlan
from wireframe.domain.shared.ids import WireframePlanId, WireframePlanLineageId

__all__ = ["WireframeEngine"]


class WireframeEngine:
    """Runs the wireframe-planning pipeline and persists a wireframe plan."""

    def __init__(
        self,
        *,
        ia: IAInputPort,
        ux: UXInputPort,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        synthesis: WireframeSynthesisPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        ordering_resolver: OrderingResolver | None = None,
        approval_planner: ApprovalPlanner | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._ia = ia
        self._ux = ux
        self._business_strategy = business_strategy
        self._brand = brand
        self._psychology = psychology
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
        self._ordering = ordering_resolver or OrderingResolver()
        self._approval = approval_planner or ApprovalPlanner()
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildWireframePlan) -> WireframePlan:
        """Run the full pipeline and persist the resulting plan."""
        now = self._clock.now()

        # 1. Assemble inputs from every signal port.
        wf_input = await self._input.assemble(
            command.request,
            ia=self._ia,
            ux=self._ux,
            business_strategy=self._business_strategy,
            brand=self._brand,
            psychology=self._psychology,
            knowledge=self._knowledge,
            research=self._research,
            competitor=self._competitor,
            reasoning=self._reasoning,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(wf_input.signals)

        # 3–4. Synthesise the plan structure, then validate its grounding.
        draft = await self._synthesis.draft(wf_input, evidence)
        self._draft_validator.validate(draft, evidence)

        # 5. Resolve the deterministic execution order (topological sort; rejects cycles).
        ordered = self._ordering.resolve(draft.blueprint)

        # 6. Wire the approval plan from section dependencies.
        blueprint, approval_plan = self._approval.plan(ordered)

        # 7. Build the six graphs.
        graphs = self._graphs.build(blueprint, approval_plan)

        # 8. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(blueprint, approval_plan, graphs)
        plan = WireframePlan(
            id=WireframePlanId.new(),
            lineage_id=command.lineage_id or WireframePlanLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=command.request.project_id,
            blueprint=blueprint,
            approval_plan=approval_plan,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.plans.save(plan)
            await uow.commit()
        return plan

    async def _next_version(self, lineage_id: WireframePlanLineageId | None) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.plans.history(lineage_id)
        return len(history) + 1
