"""The deterministic, rule-based Execution Planner — the default orchestrator brain.

Implements :class:`ExecutionPlannerPort` without any LLM: it turns the codified
:data:`~design_orchestrator.infrastructure.adapters.plan_baseline.PAGE_BLUEPRINTS` into cited
domain page and section plans, restricted to the pages in the brief and grounded in the
consolidated evidence. It is fully deterministic — the same input and evidence always yield the
same ordered plan — so the engine's output is reproducible and auditable.

It selects, never invents: every component, variant, and token key comes from the rulebook (which
is expressed in Design System terms), and every section cites real evidence ids drawn from the
graph it is given, spread across the upstream provenances so the produced execution graph can be
explained back to every engine that grounded the plan. When evidence for a preferred provenance
is absent it falls back to any available evidence, so grounding never fabricates.

Pure infrastructure: the baseline data, the domain models, and the application contracts/ports.
"""

from __future__ import annotations

from design_orchestrator.application.contracts import ExecutionDraft, OrchestrationInput
from design_orchestrator.application.ports.execution_planner import ExecutionPlannerPort
from design_orchestrator.domain.evidence.evidence import Citation, DOEvidence, EvidenceGraph
from design_orchestrator.domain.plan.choice import (
    LayoutRule,
    SpacingRule,
    TypographyChoice,
    VisualChoice,
)
from design_orchestrator.domain.plan.directives import (
    AccessibilityDirective,
    AnimationDirective,
    PerformanceDirective,
    ResponsiveDirective,
)
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.plan.section import SectionPlan
from design_orchestrator.domain.shared.ids import LayoutRegionId, PagePlanId, SectionPlanId
from design_orchestrator.domain.shared.value_objects import (
    ConsideredAlternative,
    ProvenanceKind,
    Rank,
)
from design_orchestrator.infrastructure.adapters.plan_baseline import (
    PAGE_BLUEPRINTS,
    SectionBlueprint,
)

__all__ = ["RuleBasedExecutionPlanner"]

# The provenances the planner spreads section citations across, so every upstream engine that
# grounded the plan surfaces in the execution graph nodes.
_PROVENANCE_CYCLE = (
    ProvenanceKind.WIREFRAME,
    ProvenanceKind.COMPONENT_INTELLIGENCE,
    ProvenanceKind.DESIGN_SYSTEM,
    ProvenanceKind.DESIGN_LANGUAGE,
    ProvenanceKind.UX_STRATEGY,
    ProvenanceKind.PSYCHOLOGY,
    ProvenanceKind.INFORMATION_ARCHITECTURE,
    ProvenanceKind.BUSINESS_STRATEGY,
    ProvenanceKind.BRAND_STRATEGY,
    ProvenanceKind.CREATIVE_DIRECTOR,
    ProvenanceKind.KNOWLEDGE,
)


class _CiteSource:
    """Picks real evidence, preferring given provenances, falling back to any."""

    def __init__(self, evidence: EvidenceGraph) -> None:
        self._by_prov: dict[ProvenanceKind, list[DOEvidence]] = {}
        for item in evidence:
            self._by_prov.setdefault(item.provenance, []).append(item)
        self._any: list[DOEvidence] = list(evidence)

    def cite(self, *preferred: ProvenanceKind) -> tuple[Citation, ...]:
        for provenance in preferred:
            bucket = self._by_prov.get(provenance)
            if bucket:
                return (Citation(evidence_id=bucket[0].id, relevance="grounds this choice"),)
        if self._any:
            return (Citation(evidence_id=self._any[0].id, relevance="grounds this choice"),)
        return ()


class RuleBasedExecutionPlanner(ExecutionPlannerPort):
    """A deterministic planner that grounds the codified rulebook in evidence."""

    def __init__(self, blueprints=PAGE_BLUEPRINTS) -> None:
        self._blueprints = blueprints

    async def plan(
        self, orchestration_input: OrchestrationInput, evidence: EvidenceGraph
    ) -> ExecutionDraft:
        cite = _CiteSource(evidence)
        counter = 0
        pages: list[PagePlan] = []
        for page_type in orchestration_input.brief.pages:
            blueprints = self._blueprints.get(page_type)
            if not blueprints:
                continue
            sections: list[SectionPlan] = []
            for index, blueprint in enumerate(blueprints, start=1):
                provenance = _PROVENANCE_CYCLE[counter % len(_PROVENANCE_CYCLE)]
                counter += 1
                sections.append(
                    self._section(page_type, index, blueprint, cite, provenance)
                )
            pages.append(
                PagePlan(
                    id=PagePlanId.new(),
                    page_type=page_type,
                    region_id=LayoutRegionId.new(),
                    sections=tuple(sections),
                )
            )
        return ExecutionDraft(pages=tuple(pages))

    def _section(
        self,
        page_type,
        order: int,
        bp: SectionBlueprint,
        cite: _CiteSource,
        provenance: ProvenanceKind,
    ) -> SectionPlan:
        bindings = tuple(
            dict.fromkeys(
                [
                    bp.heading_token,
                    bp.body_token,
                    bp.gap_token,
                    bp.block_token,
                    *bp.surface_tokens,
                    bp.duration_token,
                    bp.easing_token,
                ]
            )
        )
        alternative = (
            ConsideredAlternative(option=bp.alternative[0], reason_rejected=bp.alternative[1])
            if bp.alternative
            else None
        )
        return SectionPlan(
            id=SectionPlanId.new(),
            page_type=page_type,
            order=Rank(order),
            role=bp.role,
            component=bp.component,
            variant_name=bp.variant,
            layout=LayoutRule(
                mode=bp.layout_mode,
                alignment=bp.alignment,
                density=bp.density,
                columns=bp.columns,
            ),
            spacing=SpacingRule(gap_token=bp.gap_token, block_token=bp.block_token),
            typography=TypographyChoice(heading_token=bp.heading_token, body_token=bp.body_token),
            visual=VisualChoice(
                theme_mode=bp.theme_mode,
                surface_tokens=bp.surface_tokens,
                emphasis=bp.emphasis,
            ),
            token_bindings=bindings,
            responsive=ResponsiveDirective(behavior=dict(bp.responsive)),
            animation=AnimationDirective(
                duration_token=bp.duration_token,
                easing_token=bp.easing_token,
                trigger=bp.trigger,
            ),
            accessibility=AccessibilityDirective(
                role=bp.a11y_role, keyboard=bp.keyboard, min_contrast=bp.min_contrast
            ),
            performance=PerformanceDirective(
                lazy_load=bp.lazy_load, priority=bp.priority, blocks_lcp=bp.blocks_lcp
            ),
            considered_alternative=alternative,
            citations=cite.cite(provenance, ProvenanceKind.DESIGN_SYSTEM),
        )
