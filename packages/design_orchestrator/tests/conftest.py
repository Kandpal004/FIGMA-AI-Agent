"""Shared fixtures for the Design Orchestrator Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.application.ports.clock import Clock
from design_orchestrator.application.request import OrchestrationRequest
from design_orchestrator.domain.context.context import (
    OrchestrationBrief,
    ProjectContext,
    SourceRefs,
)
from design_orchestrator.domain.shared.value_objects import PageType, ProvenanceKind
from design_orchestrator.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryComponentIntelligenceInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryDesignSystemInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from design_orchestrator.infrastructure.container import build_in_memory_environment

FIXED_NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return FIXED_NOW


def signal(
    provenance: ProvenanceKind, ref: str, claim: str, confidence: float, *tags: str
) -> RawSignal:
    return RawSignal(
        provenance=provenance, external_ref=ref, claim=claim,
        confidence=confidence, source_name=provenance.value, tags=tags,
    )


@pytest.fixture
def signals() -> list[RawSignal]:
    """A rich, cross-provenance signal set covering the plan's grounding needs."""
    P = ProvenanceKind
    return [
        signal(P.DESIGN_SYSTEM, "ds1", "Bind only declared tokens and variants", 0.9,
               "token", "binding", "variant"),
        signal(P.COMPONENT_INTELLIGENCE, "ci1", "Included components and their placement", 0.9,
               "component", "placement", "order"),
        signal(P.WIREFRAME, "w1", "Page set and section order", 0.9,
               "order", "section", "structure", "page"),
        signal(P.CREATIVE_DIRECTOR, "cd1", "Gate the plan before generation", 0.9,
               "review", "gate", "quality", "checkpoint"),
        signal(P.DESIGN_LANGUAGE, "dl1", "Premium restrained visual language", 0.85,
               "visual", "typography", "emphasis"),
        signal(P.INFORMATION_ARCHITECTURE, "ia1", "Pages the plan must cover", 0.85,
               "page", "coverage", "hierarchy"),
        signal(P.UX_STRATEGY, "ux1", "Keyboard and WCAG AA everywhere", 0.9,
               "accessibility", "contrast", "focus", "interaction"),
        signal(P.PSYCHOLOGY, "p1", "Trust precedes the conversion ask", 0.9,
               "trust", "conversion", "sequence"),
        signal(P.BRAND_STRATEGY, "br1", "Brand shapes hero emphasis", 0.85,
               "brand", "emphasis", "visual"),
        signal(P.BUSINESS_STRATEGY, "b1", "Prioritise above the fold; defer below", 0.9,
               "performance", "priority", "conversion"),
        signal(P.KNOWLEDGE, "k1", "Above-the-fold sequencing best-practice", 0.85,
               "order", "sequence", "orchestration"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        pages: tuple[PageType, ...] | None = None,
        market: str = "premium",
    ) -> OrchestrationRequest:
        brief = (
            OrchestrationBrief(product_category=product_category, pages=pages)
            if pages is not None
            else OrchestrationBrief(product_category=product_category)
        )
        return OrchestrationRequest(
            brief=brief,
            project=ProjectContext(project_id="proj-x", platform="shopify_plus", market=market),
            source_refs=SourceRefs(design_system_spec_id="ds1", wireframe_plan_id="wf1"),
        )

    return _make


@pytest.fixture
def make_section():
    """Factory for a well-formed section plan (for domain-level tests)."""

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
    from design_orchestrator.domain.plan.section import SectionPlan
    from design_orchestrator.domain.shared.ids import SectionPlanId
    from design_orchestrator.domain.shared.value_objects import (
        Breakpoint,
        ComponentType,
        LayoutMode,
        PageType,
        Rank,
        SectionRole,
        ThemeMode,
    )

    def _make(order, component, page=PageType.PRODUCT):
        return SectionPlan(
            id=SectionPlanId.new(), page_type=page, order=Rank(order), role=SectionRole.CONTENT,
            component=component, variant_name="regular",
            layout=LayoutRule(mode=LayoutMode.STACK),
            spacing=SpacingRule("space.4", "space.8"),
            typography=TypographyChoice("type.h1", "type.body"),
            visual=VisualChoice(theme_mode=ThemeMode.LIGHT,
                                surface_tokens=("color.bg.default",), emphasis=2),
            token_bindings=("color.bg.default", "space.4", "space.8", "type.h1", "type.body",
                            "motion.duration.base", "motion.ease.standard"),
            responsive=ResponsiveDirective({Breakpoint.MOBILE: "stacked"}),
            animation=AnimationDirective("motion.duration.base", "motion.ease.standard"),
            accessibility=AccessibilityDirective(role="region", keyboard=("tab",)),
            performance=PerformanceDirective(priority=3),
        )

    return _make


@pytest.fixture
def built_plan(signals):
    """A real plan built through the in-memory engine (for aggregate-level tests)."""
    import asyncio

    from design_orchestrator.application.commands import BuildExecutionPlan

    env = build_in_memory_environment(clock=FixedClock(), **_ports(signals))
    request = OrchestrationRequest(
        brief=OrchestrationBrief(product_category="skincare"),
        project=ProjectContext(project_id="proj-x"),
        source_refs=SourceRefs(design_system_spec_id="ds1"),
    )
    return asyncio.run(env.engine.build(BuildExecutionPlan(request=request)))


def _ports(signals_list):
    buckets: dict[ProvenanceKind, list[RawSignal]] = {p: [] for p in ProvenanceKind}
    for s in signals_list:
        buckets.setdefault(s.provenance, []).append(s)
    P = ProvenanceKind
    return dict(
        design_system=InMemoryDesignSystemInput(buckets[P.DESIGN_SYSTEM]),
        component_intelligence=InMemoryComponentIntelligenceInput(buckets[P.COMPONENT_INTELLIGENCE]),
        wireframe=InMemoryWireframeInput(buckets[P.WIREFRAME]),
        creative_director=InMemoryCreativeDirectorInput(buckets[P.CREATIVE_DIRECTOR]),
        design_language=InMemoryDesignLanguageInput(buckets[P.DESIGN_LANGUAGE]),
        ia=InMemoryIAInput(buckets[P.INFORMATION_ARCHITECTURE]),
        ux=InMemoryUXInput(buckets[P.UX_STRATEGY]),
        psychology=InMemoryPsychologyInput(buckets[P.PSYCHOLOGY]),
        brand=InMemoryBrandInput(buckets[P.BRAND_STRATEGY]),
        business_strategy=InMemoryBusinessStrategyInput(buckets[P.BUSINESS_STRATEGY]),
        knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
    )


@pytest.fixture
def env_factory():
    """Build an in-memory environment whose input ports return the given signals."""

    def _make(signals_list=()):
        buckets: dict[ProvenanceKind, list[RawSignal]] = {p: [] for p in ProvenanceKind}
        for s in signals_list:
            buckets.setdefault(s.provenance, []).append(s)
        P = ProvenanceKind
        return build_in_memory_environment(
            design_system=InMemoryDesignSystemInput(buckets[P.DESIGN_SYSTEM]),
            component_intelligence=InMemoryComponentIntelligenceInput(
                buckets[P.COMPONENT_INTELLIGENCE]
            ),
            wireframe=InMemoryWireframeInput(buckets[P.WIREFRAME]),
            creative_director=InMemoryCreativeDirectorInput(buckets[P.CREATIVE_DIRECTOR]),
            design_language=InMemoryDesignLanguageInput(buckets[P.DESIGN_LANGUAGE]),
            ia=InMemoryIAInput(buckets[P.INFORMATION_ARCHITECTURE]),
            ux=InMemoryUXInput(buckets[P.UX_STRATEGY]),
            psychology=InMemoryPsychologyInput(buckets[P.PSYCHOLOGY]),
            brand=InMemoryBrandInput(buckets[P.BRAND_STRATEGY]),
            business_strategy=InMemoryBusinessStrategyInput(buckets[P.BUSINESS_STRATEGY]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
            clock=FixedClock(),
        )

    return _make
