"""The DesignLanguageEngine — the orchestrator of the visual-language pipeline.

Given a command, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → design the language (through the designer port) → validate grounding → build the
rules → build the two graphs → build the explanation → score → assemble — producing a single,
provenance-tracked, immutable, versioned :class:`DesignLanguageSpecification`.

It NEVER generates UI or Figma or concrete values; it defines the *visual language* only. The
pipeline is deterministic apart from the input and designer ports. Because the specification
validates provenance and the graph primitive rejects cycles, an ungrounded or structurally
broken language cannot be produced. Every collaborator is injected, so the engine is
framework-independent and testable with fakes.

The designer *proposes* the language and the deterministic stages *dispose* — the port
proposes, the domain disposes.
"""

from __future__ import annotations

from design_language.application.commands import BuildDesignLanguage
from design_language.application.pipeline.draft_validator import DraftValidator
from design_language.application.pipeline.evidence_consolidator import EvidenceConsolidator
from design_language.application.pipeline.explanation_builder import ExplanationBuilder
from design_language.application.pipeline.graph_builder import GraphBuilder
from design_language.application.pipeline.input_assembler import InputAssembler
from design_language.application.pipeline.quality_scorer import QualityScorer
from design_language.application.pipeline.rules_builder import RulesBuilder
from design_language.application.ports.brand_input import BrandInputPort
from design_language.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_language.application.ports.clock import Clock
from design_language.application.ports.competitor_insight import CompetitorInsightPort
from design_language.application.ports.creative_director_input import CreativeDirectorInputPort
from design_language.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_language.application.ports.language_designer import LanguageDesignerPort
from design_language.application.ports.psychology_input import PsychologyInputPort
from design_language.application.ports.research_input import ResearchInputPort
from design_language.application.ports.unit_of_work import UnitOfWorkFactory
from design_language.domain.report.report import DesignLanguageSpecification
from design_language.domain.shared.ids import (
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
)

__all__ = ["DesignLanguageEngine"]


class DesignLanguageEngine:
    """Runs the visual-language pipeline and persists a specification."""

    def __init__(
        self,
        *,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        creative_director: CreativeDirectorInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        designer: LanguageDesignerPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        rules_builder: RulesBuilder | None = None,
        graph_builder: GraphBuilder | None = None,
        explanation_builder: ExplanationBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._business_strategy = business_strategy
        self._brand = brand
        self._psychology = psychology
        self._creative_director = creative_director
        self._knowledge = knowledge
        self._research = research
        self._competitor = competitor
        self._designer = designer
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._validator = draft_validator or DraftValidator()
        self._rules = rules_builder or RulesBuilder()
        self._graphs = graph_builder or GraphBuilder()
        self._explanation = explanation_builder or ExplanationBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildDesignLanguage) -> DesignLanguageSpecification:
        """Run the full pipeline and persist the resulting specification."""
        now = self._clock.now()
        request = command.request

        # 1. Assemble inputs from every signal port.
        language_input = await self._input.assemble(
            request,
            business_strategy=self._business_strategy, brand=self._brand,
            psychology=self._psychology, creative_director=self._creative_director,
            knowledge=self._knowledge, research=self._research, competitor=self._competitor,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(language_input.signals)

        # 3–4. Design the language, then validate its grounding.
        draft = await self._designer.design(language_input, evidence)
        self._validator.validate(draft, evidence)

        # 5. Derive the rules and constraints.
        consistency, composition, constraints = self._rules.build(draft, evidence)

        # 6–7. Build the two graphs and the explanation.
        graphs = self._graphs.build(draft, constraints)
        explanation = self._explanation.build(draft.language_selection)

        # 8. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(
            draft, consistency, composition, constraints, graphs, evidence
        )
        specification = DesignLanguageSpecification(
            id=DesignLanguageSpecId.new(),
            lineage_id=command.lineage_id or DesignLanguageSpecLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=request.project_id,
            industry=request.brief.industry,
            visual_dna=draft.visual_dna,
            tokens=draft.tokens,
            philosophies=draft.philosophies,
            personalities=draft.personalities,
            grid_system=draft.grid_system,
            responsive_strategy=draft.responsive_strategy,
            language_selection=draft.language_selection,
            consistency_rules=consistency,
            composition_rules=composition,
            constraints=constraints,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            explanation=explanation,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.specifications.save(specification)
            await uow.commit()
        return specification

    async def _next_version(
        self, lineage_id: DesignLanguageSpecLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.specifications.history(lineage_id)
        return len(history) + 1
