"""The FigmaDesignEngine — the orchestrator of the Figma-modelling pipeline.

Given a command, it runs the full pipeline in fixed order — assemble inputs → consolidate evidence
→ compose the file (through the composer port) → validate grounding → resolve the variable/style/
instance bindings → build the five graphs → score → assemble — producing a single,
provenance-tracked, immutable, versioned :class:`FigmaDesignModel`.

It NEVER renders and imports no Figma SDK, MCP client, or HTTP library; it models the Figma
*semantics*. The pipeline is deterministic apart from the input and composer ports. Because the
model validates provenance and reference integrity, and the graph primitive rejects cycles, an
ungrounded or inconsistent model cannot be produced. Every collaborator is injected, so the engine
is framework-independent and testable with fakes.

The composer *proposes* the file and the deterministic stages *dispose* — the port proposes, the
domain disposes, and nothing enters the model without a cited, upstream-resolvable reason.
"""

from __future__ import annotations

from figma_design.application.commands import BuildFigmaDesign
from figma_design.application.pipeline.binding_resolver import BindingResolver
from figma_design.application.pipeline.draft_validator import DraftValidator
from figma_design.application.pipeline.evidence_consolidator import EvidenceConsolidator
from figma_design.application.pipeline.graph_builder import GraphBuilder
from figma_design.application.pipeline.input_assembler import InputAssembler
from figma_design.application.pipeline.quality_scorer import QualityScorer
from figma_design.application.ports.clock import Clock
from figma_design.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from figma_design.application.ports.creative_director_input import CreativeDirectorInputPort
from figma_design.application.ports.design_language_input import DesignLanguageInputPort
from figma_design.application.ports.design_orchestrator_input import DesignOrchestratorInputPort
from figma_design.application.ports.design_system_input import DesignSystemInputPort
from figma_design.application.ports.figma_composer import FigmaComposerPort
from figma_design.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from figma_design.application.ports.unit_of_work import UnitOfWorkFactory
from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.shared.ids import (
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
)

__all__ = ["FigmaDesignEngine"]


class FigmaDesignEngine:
    """Runs the Figma-modelling pipeline and persists a design model."""

    def __init__(
        self,
        *,
        design_orchestrator: DesignOrchestratorInputPort,
        design_system: DesignSystemInputPort,
        component_intelligence: ComponentIntelligenceInputPort,
        design_language: DesignLanguageInputPort,
        creative_director: CreativeDirectorInputPort,
        knowledge: KnowledgeAdvisorPort,
        composer: FigmaComposerPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        binding_resolver: BindingResolver | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._design_orchestrator = design_orchestrator
        self._design_system = design_system
        self._component_intelligence = component_intelligence
        self._design_language = design_language
        self._creative_director = creative_director
        self._knowledge = knowledge
        self._composer = composer
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._validator = draft_validator or DraftValidator()
        self._resolver = binding_resolver or BindingResolver()
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildFigmaDesign) -> FigmaDesignModel:
        """Run the full pipeline and persist the resulting model."""
        now = self._clock.now()
        request = command.request

        # 1. Assemble inputs from every signal port.
        figma_input = await self._input.assemble(
            request,
            design_orchestrator=self._design_orchestrator,
            design_system=self._design_system,
            component_intelligence=self._component_intelligence,
            design_language=self._design_language,
            creative_director=self._creative_director,
            knowledge=self._knowledge,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(figma_input.signals)

        # 3–4. Compose the file, then validate its grounding.
        draft = await self._composer.compose(figma_input, evidence)
        self._validator.validate(draft, evidence)

        # 5. Resolve the variable/style/instance bindings (unresolvable refs rejected here).
        bindings = self._resolver.resolve(draft)

        # 6. Build the five graphs.
        graphs = self._graphs.build(draft)

        # 7. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(
            draft.pages,
            draft.collections,
            draft.component_sets,
            evidence,
            bindings.reference_integrity,
        )
        model = FigmaDesignModel(
            id=FigmaDesignModelId.new(),
            lineage_id=command.lineage_id or FigmaDesignModelLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=request.project_id,
            source_refs=figma_input.source_refs,
            pages=draft.pages,
            collections=draft.collections,
            style_set=draft.style_set,
            component_sets=draft.component_sets,
            token_mapping=bindings.token_mapping,
            variant_mapping=bindings.variant_mapping,
            graphs=graphs,
            evidence_graph=evidence,
            quality=quality,
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.models.save(model)
            await uow.commit()
        return model

    async def _next_version(
        self, lineage_id: FigmaDesignModelLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.models.history(lineage_id)
        return len(history) + 1
