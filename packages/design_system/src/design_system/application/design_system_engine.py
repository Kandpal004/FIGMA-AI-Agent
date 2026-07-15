"""The DesignSystemEngine — the orchestrator of the design-system pipeline.

Given a command, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → architect the token system (through the brain port) → validate grounding → resolve
and integrity-check the tokens → build the constraints → build the six graphs → score →
assemble — producing a single, provenance-tracked, immutable, versioned
:class:`DesignSystemSpecification`.

It NEVER generates UI or Figma; it specifies the design system every future UI must follow. The
pipeline is deterministic apart from the input and brain ports. Because the specification
validates provenance and token integrity, and the graph primitive rejects cycles, a random or
inconsistent design system cannot be produced. Every collaborator is injected, so the engine is
framework-independent and testable with fakes.

The architect *proposes* tokens and components and the deterministic stages *dispose* — the port
proposes, the domain disposes, and nothing enters the system without a cited reason.
"""

from __future__ import annotations

from design_system.application.commands import BuildDesignSystem
from design_system.application.pipeline.constraint_builder import ConstraintBuilder
from design_system.application.pipeline.draft_validator import DraftValidator
from design_system.application.pipeline.evidence_consolidator import EvidenceConsolidator
from design_system.application.pipeline.graph_builder import GraphBuilder
from design_system.application.pipeline.input_assembler import InputAssembler
from design_system.application.pipeline.quality_scorer import QualityScorer
from design_system.application.pipeline.token_resolver import TokenResolver
from design_system.application.ports.brand_input import BrandInputPort
from design_system.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_system.application.ports.clock import Clock
from design_system.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from design_system.application.ports.creative_director_input import CreativeDirectorInputPort
from design_system.application.ports.design_language_input import DesignLanguageInputPort
from design_system.application.ports.ia_input import IAInputPort
from design_system.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_system.application.ports.psychology_input import PsychologyInputPort
from design_system.application.ports.token_architect import TokenArchitectPort
from design_system.application.ports.unit_of_work import UnitOfWorkFactory
from design_system.application.ports.ux_input import UXInputPort
from design_system.application.ports.wireframe_input import WireframeInputPort
from design_system.domain.report.report import DesignSystemSpecification
from design_system.domain.shared.ids import (
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
)

__all__ = ["DesignSystemEngine"]


class DesignSystemEngine:
    """Runs the design-system pipeline and persists a specification."""

    def __init__(
        self,
        *,
        design_language: DesignLanguageInputPort,
        component_intelligence: ComponentIntelligenceInputPort,
        creative_director: CreativeDirectorInputPort,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        ux: UXInputPort,
        ia: IAInputPort,
        wireframe: WireframeInputPort,
        knowledge: KnowledgeAdvisorPort,
        architect: TokenArchitectPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        draft_validator: DraftValidator | None = None,
        token_resolver: TokenResolver | None = None,
        constraint_builder: ConstraintBuilder | None = None,
        graph_builder: GraphBuilder | None = None,
        scorer: QualityScorer | None = None,
    ) -> None:
        self._design_language = design_language
        self._component_intelligence = component_intelligence
        self._creative_director = creative_director
        self._business_strategy = business_strategy
        self._brand = brand
        self._psychology = psychology
        self._ux = ux
        self._ia = ia
        self._wireframe = wireframe
        self._knowledge = knowledge
        self._architect = architect
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._validator = draft_validator or DraftValidator()
        self._resolver = token_resolver or TokenResolver()
        self._constraints = constraint_builder or ConstraintBuilder()
        self._graphs = graph_builder or GraphBuilder()
        self._scorer = scorer or QualityScorer()

    async def build(self, command: BuildDesignSystem) -> DesignSystemSpecification:
        """Run the full pipeline and persist the resulting specification."""
        now = self._clock.now()
        request = command.request

        # 1. Assemble inputs from every signal port.
        design_input = await self._input.assemble(
            request,
            design_language=self._design_language,
            component_intelligence=self._component_intelligence,
            creative_director=self._creative_director,
            business_strategy=self._business_strategy,
            brand=self._brand,
            psychology=self._psychology,
            ux=self._ux,
            ia=self._ia,
            wireframe=self._wireframe,
            knowledge=self._knowledge,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(design_input.signals)

        # 3–4. Architect the token system, then validate its grounding.
        draft = await self._architect.architect(design_input, evidence)
        self._validator.validate(draft, evidence)

        # 5. Resolve and integrity-check the tokens (dangling refs / cycles rejected here).
        token_integrity = self._resolver.resolve(draft)

        # 6. Derive the enforced constraints.
        constraints = self._constraints.build(draft, evidence)

        # 7. Build the six graphs.
        graphs = self._graphs.build(
            draft.token_set, draft.component_specs, draft.theme_set, constraints
        )

        # 8. Score and assemble (the aggregate's invariants fire here).
        quality = self._scorer.score(
            draft.token_set,
            draft.component_specs,
            draft.theme_set,
            constraints,
            graphs,
            evidence,
            token_integrity,
        )
        specification = DesignSystemSpecification(
            id=DesignSystemSpecId.new(),
            lineage_id=command.lineage_id or DesignSystemSpecLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=request.project_id,
            token_set=draft.token_set,
            typography=draft.typography,
            spacing=draft.spacing,
            radius=draft.radius,
            elevation=draft.elevation,
            shadow=draft.shadow,
            border=draft.border,
            breakpoints=draft.breakpoints,
            grid=draft.grid,
            container=draft.container,
            motion=draft.motion,
            interaction=draft.interaction,
            states=draft.states,
            component_specs=draft.component_specs,
            theme_set=draft.theme_set,
            localization=draft.localization,
            constraint_set=constraints,
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
        self, lineage_id: DesignSystemSpecLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.specifications.history(lineage_id)
        return len(history) + 1
