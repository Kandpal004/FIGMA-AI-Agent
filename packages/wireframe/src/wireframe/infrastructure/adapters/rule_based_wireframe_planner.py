"""RuleBasedWireframePlanner — the deterministic planner brain (default synthesis).

Implements :class:`WireframeSynthesisPort` by mapping the codified page blueprints
(:mod:`page_blueprints`) onto fully-specified :class:`SectionPlan` s over the supplied
evidence, citing real evidence ids for every section, block, component, and approval
requirement. It is fully deterministic (same input + evidence ⇒ same draft), dependency-free,
and honest — it invents no facts; it *structures* the plan over the evidence it is given and
grounds each decision by citing it.

It grounds a section's structure in the Information Architecture, its goals in Business
Strategy, its trust posture in Customer Psychology, and its components in the Knowledge
Engine — so the plan visibly references the upstream engines the spec requires. It applies
baseline responsive, accessibility, SEO, performance, criteria, and review requirements to
every section, so each produced section is fully specified without repeating boilerplate in
the knowledge base. It draws nothing — it plans.
"""

from __future__ import annotations

from collections.abc import Sequence

from wireframe.application.contracts import WireframeDraft, WireframeInput
from wireframe.domain.approval.approval import ApprovalRequirement
from wireframe.domain.block.block import Block
from wireframe.domain.component.component import ComponentRequirement, DataContractIntent
from wireframe.domain.context.context import WireframeBrief
from wireframe.domain.evidence.evidence import EvidenceGraph, WFEvidence
from wireframe.domain.page.page_plan import PagePlan
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.section.criteria import ChecklistItem, FailureCriterion, SectionIO, SuccessCriterion
from wireframe.domain.section.goals import SectionGoals
from wireframe.domain.section.requirements import (
    AccessibilityRequirement,
    AssetRequirement,
    DataRequirement,
    InteractionRequirement,
    PerformanceConsideration,
    ResponsiveBehaviour,
    ResponsiveRule,
    SEORequirement,
)
from wireframe.domain.section.section_plan import SectionPlan
from wireframe.domain.shared.ids import (
    ApprovalReqId,
    BlockId,
    ComponentReqId,
    PagePlanId,
    SectionId,
    WFEvidenceId,
)
from wireframe.domain.shared.value_objects import (
    AccessibilityKind,
    AssetKind,
    BlockKind,
    Breakpoint,
    IOKind,
    PageType,
    PerformanceKind,
    Priority,
    ProvenanceKind,
    RequirementLevel,
    ResponsiveIntent,
    SEOKind,
    SectionType,
)
from wireframe.infrastructure.adapters.page_blueprints import (
    ComponentSpec,
    SectionSpec,
    spec_for,
)

__all__ = ["RuleBasedWireframePlanner"]

_MEDIA_BLOCKS = frozenset({BlockKind.MEDIA, BlockKind.HERO, BlockKind.PRODUCT})
_FORM_BLOCKS = frozenset({BlockKind.FORM})
_BASELINE_RESPONSIVE = (
    ResponsiveRule(Breakpoint.MOBILE, ResponsiveIntent.STACK),
    ResponsiveRule(Breakpoint.TABLET, ResponsiveIntent.REFLOW),
    ResponsiveRule(Breakpoint.DESKTOP, ResponsiveIntent.RETAIN),
)


class RuleBasedWireframePlanner:
    """A deterministic, evidence-grounded implementation of the synthesis port."""

    async def draft(
        self, wf_input: WireframeInput, evidence: EvidenceGraph
    ) -> WireframeDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        pages = tuple(
            self._page(page_type, ranked)
            for page_type in self._page_types(wf_input.brief)
        )
        return WireframeDraft(blueprint=PlanBlueprint.of(pages))

    # ------------------------------------------------------------------ #
    @staticmethod
    def _page_types(brief: WireframeBrief) -> tuple[PageType, ...]:
        page_types = list(brief.pages)
        if brief.has_blog and PageType.BLOG not in page_types:
            page_types.append(PageType.BLOG)
        if brief.has_landing and PageType.LANDING not in page_types:
            page_types.append(PageType.LANDING)
        return tuple(page_types)

    # -- citation helpers -------------------------------------------------- #
    @staticmethod
    def _cite_prefer(
        ranked: Sequence[WFEvidence],
        provenance: ProvenanceKind,
        keywords: Sequence[str],
        limit: int = 2,
    ) -> tuple[WFEvidenceId, ...]:
        """Cite the keywords, grounding the decision in ``provenance`` first.

        A section's structure is grounded in the Information Architecture, its goals in
        Business Strategy, its trust posture in Psychology, and its components in Knowledge —
        so the plan cites the source that actually justifies each decision, not merely the
        highest-confidence evidence. Falls back to the strongest evidence so no decision is
        left ungrounded.
        """
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]

        def matches(e: WFEvidence) -> bool:
            hay = f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
            return any(k in hay for k in kws)

        preferred = [e for e in ranked if e.provenance is provenance and matches(e)]
        others = [e for e in ranked if e.provenance is not provenance and matches(e)]
        chosen = (preferred + others)[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)

    # -- page & section ---------------------------------------------------- #
    def _page(self, page_type: PageType, ranked: Sequence[WFEvidence]) -> PagePlan:
        spec = spec_for(page_type)
        # First pass: stable id per section type, for dependency resolution.
        type_to_id: dict[SectionType, SectionId] = {}
        for section_spec in spec.sections:
            type_to_id.setdefault(section_spec.type, SectionId.new())
        sections = tuple(
            self._section(section_spec, type_to_id, ranked)
            for section_spec in spec.sections
        )
        page_cite = self._cite_prefer(
            ranked, ProvenanceKind.INFORMATION_ARCHITECTURE,
            (page_type.value, "page", "structure", "navigation"), 2,
        )
        return PagePlan(
            id=PagePlanId.new(), page_type=page_type, purpose=spec.purpose,
            sections=sections, evidence_ids=page_cite,
        )

    def _section(
        self,
        spec: SectionSpec,
        type_to_id: dict[SectionType, SectionId],
        ranked: Sequence[WFEvidence],
    ) -> SectionPlan:
        struct_cite = self._cite_prefer(
            ranked, ProvenanceKind.INFORMATION_ARCHITECTURE,
            (spec.type.value, "section", "structure", "page", "navigation", "content"), 2,
        )
        goal_cite = self._cite_prefer(
            ranked, ProvenanceKind.BUSINESS_STRATEGY,
            ("business", "conversion", "aov", "revenue", "positioning", "goal"), 2,
        )
        trust_cite = self._cite_prefer(
            ranked, ProvenanceKind.PSYCHOLOGY,
            ("trust", "review", "objection", "anxiety", "confidence", "guarantee"), 2,
        )
        comp_cite = self._cite_prefer(
            ranked, ProvenanceKind.KNOWLEDGE,
            ("component", "pattern", "navigation", "accessibility", "structure", "layout"), 2,
        )
        # A section's blocks — its concrete content and CTAs — execute the UX strategy.
        block_cite = self._cite_prefer(
            ranked, ProvenanceKind.UX_STRATEGY,
            (spec.type.value, "page", "cta", "conversion", "goal", "navigation", "content"), 2,
        )
        section_ev = tuple(dict.fromkeys(struct_cite + goal_cite + trust_cite + block_cite))
        approval_ev = tuple(dict.fromkeys(goal_cite + trust_cite)) or struct_cite

        section_id = type_to_id[spec.type]
        block_kinds = {b.kind for b in spec.blocks}

        blocks = tuple(
            Block(
                id=BlockId.new(), kind=b.kind, label=b.label, priority=Priority(b.priority),
                is_required=b.required, data_kinds=b.data_kinds, evidence_ids=block_cite,
            )
            for b in spec.blocks
        )
        required_components = tuple(
            self._component(c, RequirementLevel.REQUIRED, comp_cite) for c in spec.required_components
        )
        optional_components = tuple(
            self._component(c, RequirementLevel.OPTIONAL, comp_cite) for c in spec.optional_components
        )
        required_data = tuple(
            DataRequirement(kind=kind, description=desc, required=True) for kind, desc in spec.data
        )
        required_assets = (
            (AssetRequirement(kind=AssetKind.IMAGE, description="Imagery for the section."),)
            if block_kinds & _MEDIA_BLOCKS
            else ()
        )
        interactions = tuple(
            InteractionRequirement(kind=kind, intent=intent) for kind, intent in spec.interactions
        )
        dependencies = tuple(
            type_to_id[dep] for dep in spec.depends_on if dep in type_to_id
        )
        approval = ApprovalRequirement(
            id=ApprovalReqId.new(), target=section_id, gate=spec.gate,
            approver_role=spec.approver,
            criteria=spec.approval_criteria + ("Every recommendation cites upstream evidence.",),
            evidence_ids=approval_ev,
        )
        return SectionPlan(
            id=section_id, type=spec.type,
            goals=SectionGoals(
                purpose=spec.purpose, business_goal=spec.business_goal,
                user_goal=spec.user_goal, conversion_goal=spec.conversion_goal,
                trust_goal=spec.trust_goal, evidence_ids=goal_cite,
            ),
            is_required=spec.required, priority=Priority(spec.priority),
            blocks=blocks,
            required_components=required_components, optional_components=optional_components,
            required_data=required_data, required_assets=required_assets,
            interaction_requirements=interactions,
            responsive_behaviour=ResponsiveBehaviour(rules=_BASELINE_RESPONSIVE),
            accessibility_requirements=self._accessibility(block_kinds),
            seo_requirements=self._seo(block_kinds),
            performance_considerations=self._performance(block_kinds),
            inputs=self._inputs(spec),
            outputs=self._outputs(spec),
            dependencies=dependencies,
            success_criteria=self._success(spec),
            failure_criteria=self._failure(),
            review_checklist=self._checklist(spec),
            approval_requirement=approval,
            evidence_ids=section_ev,
        )

    @staticmethod
    def _component(
        spec: ComponentSpec, level: RequirementLevel, cite: tuple[WFEvidenceId, ...]
    ) -> ComponentRequirement:
        contract = (
            DataContractIntent(fields=spec.fields, cardinality=spec.cardinality, data_kind=spec.data_kind)
            if spec.fields or spec.data_kind
            else None
        )
        return ComponentRequirement(
            id=ComponentReqId.new(), component=spec.component, requirement=level,
            rationale=spec.rationale, data_contract=contract, depends_on=spec.depends_on,
            evidence_ids=cite,
        )

    # -- baseline requirement builders ------------------------------------ #
    @staticmethod
    def _accessibility(block_kinds: set[BlockKind]) -> tuple[AccessibilityRequirement, ...]:
        reqs = [
            AccessibilityRequirement(AccessibilityKind.KEYBOARD, "All interactive elements are keyboard operable."),
            AccessibilityRequirement(AccessibilityKind.SCREEN_READER, "Structure exposes semantic roles and labels."),
            AccessibilityRequirement(AccessibilityKind.FOCUS_ORDER, "Focus order follows the reading order."),
        ]
        if block_kinds & _MEDIA_BLOCKS:
            reqs.append(AccessibilityRequirement(AccessibilityKind.ALT_TEXT, "Imagery carries descriptive alt text."))
        if block_kinds & _FORM_BLOCKS:
            reqs.append(AccessibilityRequirement(AccessibilityKind.LABELS, "Every field has a programmatic label."))
        return tuple(reqs)

    @staticmethod
    def _seo(block_kinds: set[BlockKind]) -> tuple[SEORequirement, ...]:
        reqs = [
            SEORequirement(SEOKind.HEADING_HIERARCHY, "Headings form a correct, single-h1 hierarchy."),
            SEORequirement(SEOKind.SEMANTIC_MARKUP, "Content uses semantic, crawlable markup."),
        ]
        if block_kinds & {BlockKind.PRODUCT, BlockKind.REVIEW}:
            reqs.append(SEORequirement(SEOKind.STRUCTURED_DATA, "Product/review structured data is emitted."))
        if block_kinds & _MEDIA_BLOCKS:
            reqs.append(SEORequirement(SEOKind.IMAGE_ALT, "Images declare descriptive alt attributes."))
        return tuple(reqs)

    @staticmethod
    def _performance(block_kinds: set[BlockKind]) -> tuple[PerformanceConsideration, ...]:
        reqs = [
            PerformanceConsideration(PerformanceKind.MINIMIZE_LAYOUT_SHIFT, "Reserve space to avoid layout shift."),
        ]
        if block_kinds & _MEDIA_BLOCKS:
            reqs.append(PerformanceConsideration(PerformanceKind.LAZY_LOAD, "Defer offscreen media loading."))
            reqs.append(PerformanceConsideration(PerformanceKind.IMAGE_OPTIMIZATION, "Serve optimized, sized images."))
        return tuple(reqs)

    @staticmethod
    def _inputs(spec: SectionSpec) -> tuple[SectionIO, ...]:
        return tuple(SectionIO(kind=IOKind.DATA, name=kind.value) for kind, _ in spec.data)

    @staticmethod
    def _outputs(spec: SectionSpec) -> tuple[SectionIO, ...]:
        outputs = [SectionIO(kind=IOKind.ARTIFACT, name=f"{spec.type.value}_section_plan")]
        outputs.extend(SectionIO(kind=IOKind.EVENT, name=k.value) for k, _ in spec.interactions)
        return tuple(outputs)

    @staticmethod
    def _success(spec: SectionSpec) -> tuple[SuccessCriterion, ...]:
        base = SuccessCriterion("The section renders its required blocks and components with real data.")
        return (base, *(SuccessCriterion(s) for s in spec.success))

    @staticmethod
    def _failure() -> tuple[FailureCriterion, ...]:
        return (
            FailureCriterion("A required block or component is missing or unpopulated."),
            FailureCriterion("The section violates keyboard access or focus order."),
        )

    @staticmethod
    def _checklist(spec: SectionSpec) -> tuple[ChecklistItem, ...]:
        base = [
            ChecklistItem("Section is keyboard accessible and screen-reader friendly."),
            ChecklistItem("Section meets its performance budget."),
            ChecklistItem("Every recommendation cites upstream evidence."),
        ]
        base.extend(ChecklistItem(c) for c in spec.checklist)
        return tuple(base)
