"""The ComponentIntelligenceEngine — the orchestrator of the component-intelligence pipeline.

Given a command, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → decide the composition (through the brain port) → validate grounding → resolve
coherence → build the rules → build the two graphs → score → assemble — producing a single,
provenance-tracked, immutable, versioned :class:`ComponentCompositionSpecification`.

It NEVER generates component code, Figma, or UI; it decides *which components and why*. The
pipeline is deterministic apart from the input and brain ports. Because the specification
validates provenance and coherence, and the graph primitive rejects cycles, a random or
incoherent composition cannot be produced. Every collaborator is injected, so the engine is
framework-independent and testable with fakes.

The brain *proposes* components and the deterministic stages *dispose* — the port proposes, the
domain disposes, and no component enters the composition without a cited business reason.
"""

from __future__ import annotations

from component_intelligence.application.commands import BuildComposition
from component_intelligence.application.pipeline.coherence_resolver import CoherenceResolver
from component_intelligence.application.pipeline.draft_validator import DraftValidator
from component_intelligence.application.pipeline.evidence_consolidator import EvidenceConsolidator
from component_intelligence.application.pipeline.graph_builder import GraphBuilder
from component_intelligence.application.pipeline.input_assembler import InputAssembler
from component_intelligence.application.pipeline.quality_scorer import QualityScorer
from component_intelligence.application.pipeline.rules_builder import RulesBuilder
from component_intelligence.application.ports.brand_input import BrandInputPort
from component_intelligence.application.ports.business_strategy_input import BusinessStrategyInputPort
from component_intelligence.application.ports.clock import Clock
from component_intelligence.application.ports.competitor_insight import CompetitorInsightPort
from component_intelligence.application.ports.component_intelligence import ComponentIntelligencePort
from component_intelligence.application.ports.creative_director_input import CreativeDirectorInputPort
from component_intelligence.application.ports.design_language_input import DesignLanguageInputPort
from component_intelligence.application.ports.ia_input import IAInputPort
from component_intelligence.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from component_intelligence.application.ports.psychology_input import PsychologyInputPort
from component_intelligence.application.ports.research_input import ResearchInputPort
from component_intelligence.application.ports.unit_of_work import UnitOfWorkFactory
from component_intelligence.application.ports.ux_input import UXInputPort
from component_intelligence.application.ports.wireframe_input import WireframeInputPort
from component_intelligence.domain.report.report import ComponentCompositionSpecification
from component_intelligence.domain.shared.ids import (
    ComponentSpecId,
    ComponentSpecLineageId,
)

__all__ = ["ComponentIntelligenceEngine"]


class ComponentIntelligenceEngine:
    """Runs the component-intelligence pipeline and persists a specification."""

    def __init__(
        self,
        *,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        ux: UXInputPort,
        ia: IAInputPort,
        wireframe: WireframeInputPort,
        creative_director: CreativeDirectorInputPort,
        design_language: DesignLanguageInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        brain: ComponentIntelligencePort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        coherence_resolver: CoherenceResolver | None = None,
        rules_builder: RulesBuilder | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._business_strategy = business_strategy
        self._brand = brand
        self._psychology = psychology
        self._ux = ux
        self._ia = ia
        self._wireframe = wireframe
        self._creative_director = creative_director
        self._design_language = design_language
        self._knowledge = knowledge
        self._research = research
        self._competitor = competitor
        self._brain = brain
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._validator = draft_validator or DraftValidator()
        self._coherence = coherence_resolver or CoherenceResolver()
        self._rules = rules_builder or RulesBuilder()
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildComposition) -> ComponentCompositionSpecification:
        """Run the full pipeline and persist the resulting specification."""
        now = self._clock.now()
        request = command.request

        # 1. Assemble inputs from every signal port.
        component_input = await self._input.assemble(
            request,
            business_strategy=self._business_strategy, brand=self._brand,
            psychology=self._psychology, ux=self._ux, ia=self._ia, wireframe=self._wireframe,
            creative_director=self._creative_director, design_language=self._design_language,
            knowledge=self._knowledge, research=self._research, competitor=self._competitor,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(component_input.signals)

        # 3–4. Decide the composition, then validate its grounding.
        draft = await self._brain.decide(component_input, evidence)
        self._validator.validate(draft, evidence)

        # 5. Resolve coherence (conflicts + dependency closure).
        composition = self._coherence.resolve(draft)
        compatibility = draft.compatibility

        # 6. Derive the rules.
        composition_rules, placement_rules, visibility_rules, responsive_rules, reuse_rules = (
            self._rules.build(composition, evidence)
        )

        # 7. Build the two graphs.
        graphs = self._graphs.build(composition, compatibility, placement_rules)

        # 8. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(
            composition, compatibility, composition_rules, placement_rules, visibility_rules,
            responsive_rules, reuse_rules, graphs, evidence,
        )
        specification = ComponentCompositionSpecification(
            id=ComponentSpecId.new(),
            lineage_id=command.lineage_id or ComponentSpecLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=request.project_id,
            composition=composition,
            compatibility=compatibility,
            composition_rules=composition_rules,
            placement_rules=placement_rules,
            visibility_rules=visibility_rules,
            responsive_rules=responsive_rules,
            reuse_rules=reuse_rules,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.specifications.save(specification)
            await uow.commit()
        return specification

    async def _next_version(
        self, lineage_id: ComponentSpecLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.specifications.history(lineage_id)
        return len(history) + 1
