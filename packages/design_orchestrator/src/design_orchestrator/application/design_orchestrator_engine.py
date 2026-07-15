"""The DesignOrchestratorEngine — the orchestrator of the orchestration pipeline.

Given a command, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → plan the ordered sections (through the planner port) → validate grounding → resolve
the token/variant bindings → build the layout → build the component tree → build the graphs →
schedule the reviews → score → assemble — producing a single, provenance-tracked, immutable,
versioned :class:`DesignExecutionPlan`.

It NEVER generates UI or Figma; it plans the *execution* every future generator replays. The
pipeline is deterministic apart from the input and planner ports. Because the plan validates
provenance and binding integrity, and the graph primitive rejects cycles, a random or
inconsistent plan cannot be produced. Every collaborator is injected, so the engine is
framework-independent and testable with fakes.

The planner *proposes* the ordered sections and the deterministic stages *dispose* — the port
proposes, the domain disposes, and nothing enters the plan without a cited, upstream-resolvable
reason.
"""

from __future__ import annotations

from design_orchestrator.application.commands import BuildExecutionPlan
from design_orchestrator.application.pipeline.draft_validator import DraftValidator
from design_orchestrator.application.pipeline.evidence_consolidator import EvidenceConsolidator
from design_orchestrator.application.pipeline.graph_builder import GraphBuilder
from design_orchestrator.application.pipeline.input_assembler import InputAssembler
from design_orchestrator.application.pipeline.layout_builder import LayoutBuilder
from design_orchestrator.application.pipeline.quality_scorer import QualityScorer
from design_orchestrator.application.pipeline.review_planner import ReviewPlanner
from design_orchestrator.application.pipeline.selection_resolver import SelectionResolver
from design_orchestrator.application.pipeline.tree_builder import TreeBuilder
from design_orchestrator.application.ports.brand_input import BrandInputPort
from design_orchestrator.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_orchestrator.application.ports.clock import Clock
from design_orchestrator.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from design_orchestrator.application.ports.creative_director_input import CreativeDirectorInputPort
from design_orchestrator.application.ports.design_language_input import DesignLanguageInputPort
from design_orchestrator.application.ports.design_system_input import DesignSystemInputPort
from design_orchestrator.application.ports.execution_planner import ExecutionPlannerPort
from design_orchestrator.application.ports.ia_input import IAInputPort
from design_orchestrator.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_orchestrator.application.ports.psychology_input import PsychologyInputPort
from design_orchestrator.application.ports.unit_of_work import UnitOfWorkFactory
from design_orchestrator.application.ports.ux_input import UXInputPort
from design_orchestrator.application.ports.wireframe_input import WireframeInputPort
from design_orchestrator.domain.report.report import DesignExecutionPlan
from design_orchestrator.domain.shared.ids import (
    DesignExecutionPlanId,
    DesignExecutionPlanLineageId,
)

__all__ = ["DesignOrchestratorEngine"]


class DesignOrchestratorEngine:
    """Runs the orchestration pipeline and persists an execution plan."""

    def __init__(
        self,
        *,
        design_system: DesignSystemInputPort,
        component_intelligence: ComponentIntelligenceInputPort,
        wireframe: WireframeInputPort,
        creative_director: CreativeDirectorInputPort,
        design_language: DesignLanguageInputPort,
        ia: IAInputPort,
        ux: UXInputPort,
        psychology: PsychologyInputPort,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        planner: ExecutionPlannerPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        selection_resolver: SelectionResolver | None = None,
        layout_builder: LayoutBuilder | None = None,
        tree_builder: TreeBuilder | None = None,
        graph_builder: GraphBuilder | None = None,
        review_planner: ReviewPlanner | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._design_system = design_system
        self._component_intelligence = component_intelligence
        self._wireframe = wireframe
        self._creative_director = creative_director
        self._design_language = design_language
        self._ia = ia
        self._ux = ux
        self._psychology = psychology
        self._brand = brand
        self._business_strategy = business_strategy
        self._knowledge = knowledge
        self._planner = planner
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._validator = draft_validator or DraftValidator()
        self._resolver = selection_resolver or SelectionResolver()
        self._layout = layout_builder or LayoutBuilder()
        self._tree = tree_builder or TreeBuilder()
        self._graphs = graph_builder or GraphBuilder()
        self._reviews = review_planner or ReviewPlanner()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildExecutionPlan) -> DesignExecutionPlan:
        """Run the full pipeline and persist the resulting plan."""
        now = self._clock.now()
        request = command.request

        # 1. Assemble inputs from every signal port.
        orchestration_input = await self._input.assemble(
            request,
            design_system=self._design_system,
            component_intelligence=self._component_intelligence,
            wireframe=self._wireframe,
            creative_director=self._creative_director,
            design_language=self._design_language,
            ia=self._ia,
            ux=self._ux,
            psychology=self._psychology,
            brand=self._brand,
            business_strategy=self._business_strategy,
            knowledge=self._knowledge,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(orchestration_input.signals)

        # 3–4. Plan the ordered sections, then validate grounding.
        draft = await self._planner.plan(orchestration_input, evidence)
        self._validator.validate(draft, evidence)

        # 5. Resolve the token/variant bindings (unresolvable selections rejected here).
        selection = self._resolver.resolve(draft)

        # 6. Build the layout model.
        layout_model, _ = self._layout.build(draft)

        # 7. Build the component tree.
        component_tree = self._tree.build(draft)

        # 8. Schedule the reviews, then build the graphs.
        review_plan = self._reviews.build(evidence)
        graphs = self._graphs.build(draft, layout_model, review_plan)

        # 9. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(
            draft.pages,
            request.brief.pages,
            graphs,
            review_plan,
            evidence,
            selection.binding_integrity,
        )
        plan = DesignExecutionPlan(
            id=DesignExecutionPlanId.new(),
            lineage_id=command.lineage_id or DesignExecutionPlanLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=request.project_id,
            source_refs=orchestration_input.source_refs,
            pages=draft.pages,
            component_tree=component_tree,
            layout_model=layout_model,
            token_mapping=selection.token_mapping,
            variant_mapping=selection.variant_mapping,
            graphs=graphs,
            review_plan=review_plan,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.plans.save(plan)
            await uow.commit()
        return plan

    async def _next_version(
        self, lineage_id: DesignExecutionPlanLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.plans.history(lineage_id)
        return len(history) + 1
