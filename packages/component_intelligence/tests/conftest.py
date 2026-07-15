"""Shared fixtures for the Component Intelligence Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from component_intelligence.application.contracts import RawSignal
from component_intelligence.application.ports.clock import Clock
from component_intelligence.application.request import ComponentIntelligenceRequest
from component_intelligence.domain.context.context import CompositionBrief, ProjectContext
from component_intelligence.domain.shared.value_objects import PageType, ProvenanceKind
from component_intelligence.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryResearchInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from component_intelligence.infrastructure.container import build_in_memory_environment

FIXED_NOW = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)


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
    """A rich, cross-provenance signal set covering the composition's grounding needs."""
    P = ProvenanceKind
    return [
        signal(P.WIREFRAME, "w1", "Product page needs gallery, buy box, variant picker, trust, reviews", 0.9, "product", "component", "section", "structure", "buy", "cart", "conversion"),
        signal(P.INFORMATION_ARCHITECTURE, "ia1", "Clear page hierarchy and structure", 0.88, "structure", "hierarchy", "page", "navigation"),
        signal(P.UX_STRATEGY, "ux1", "Smooth interaction and flow across pages", 0.9, "ux", "interaction", "flow", "goal"),
        signal(P.BUSINESS_STRATEGY, "b1", "Premium positioning; increase conversion and AOV", 0.9, "business", "positioning", "conversion", "revenue", "purpose"),
        signal(P.BRAND_STRATEGY, "br1", "Elegant restrained premium brand identity", 0.85, "brand", "identity", "tone", "trust"),
        signal(P.PSYCHOLOGY, "p1", "Reviews and guarantees reduce anxiety and build trust", 0.9, "trust", "conversion", "friction", "emotion"),
        signal(P.CREATIVE_DIRECTOR, "cd1", "Approved premium quality direction; reject generic", 0.9, "quality", "approved", "premium", "review"),
        signal(P.DESIGN_LANGUAGE, "d1", "Token system and component variants defined", 0.85, "token", "variant", "design", "language"),
        signal(P.KNOWLEDGE, "k1", "Component patterns and composition best-practice", 0.85, "component", "pattern", "composition", "compatibility"),
        signal(P.RESEARCH, "r1", "Shoppers rely on reviews and imagery", 0.8, "trust", "conversion"),
        signal(P.COMPETITOR, "c1", "Leaders use sticky add-to-cart and trust badges", 0.8, "conversion", "trust"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        pages: tuple[PageType, ...] | None = None,
        catalog_scale: str = "large",
        market: str = "premium",
    ) -> ComponentIntelligenceRequest:
        brief = (
            CompositionBrief(product_category=product_category, pages=pages, catalog_scale=catalog_scale)
            if pages is not None
            else CompositionBrief(product_category=product_category, catalog_scale=catalog_scale)
        )
        return ComponentIntelligenceRequest(
            brief=brief,
            project=ProjectContext(project_id="proj-x", platform="shopify_plus", market=market),
        )

    return _make


@pytest.fixture
def env_factory():
    """Build an in-memory environment whose input ports return the given signals."""

    def _make(signals_list=()):
        buckets: dict[ProvenanceKind, list[RawSignal]] = {p: [] for p in ProvenanceKind}
        for s in signals_list:
            buckets.setdefault(s.provenance, []).append(s)
        P = ProvenanceKind
        return build_in_memory_environment(
            wireframe=InMemoryWireframeInput(buckets[P.WIREFRAME]),
            ia=InMemoryIAInput(buckets[P.INFORMATION_ARCHITECTURE]),
            ux=InMemoryUXInput(buckets[P.UX_STRATEGY]),
            business_strategy=InMemoryBusinessStrategyInput(buckets[P.BUSINESS_STRATEGY]),
            brand=InMemoryBrandInput(buckets[P.BRAND_STRATEGY]),
            psychology=InMemoryPsychologyInput(buckets[P.PSYCHOLOGY]),
            creative_director=InMemoryCreativeDirectorInput(buckets[P.CREATIVE_DIRECTOR]),
            design_language=InMemoryDesignLanguageInput(buckets[P.DESIGN_LANGUAGE]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[P.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[P.COMPETITOR]),
            clock=FixedClock(),
        )

    return _make
