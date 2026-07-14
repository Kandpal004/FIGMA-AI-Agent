"""Shared fixtures for the Information Architecture Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ia.application.contracts import RawSignal
from ia.application.ports.clock import Clock
from ia.application.request import IARequest
from ia.domain.context.context import IABrief, ProjectContext
from ia.domain.shared.value_objects import PageType, ProvenanceKind
from ia.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryReasoning,
    InMemoryResearchInput,
    InMemoryUXInput,
)
from ia.infrastructure.container import build_in_memory_environment

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
    """A rich, cross-provenance signal set covering every default page and IA concern."""
    return [
        signal(ProvenanceKind.UX_STRATEGY, "u1", "Primary user goal: complete a confident purchase", 0.9, "goal", "user", "conversion"),
        signal(ProvenanceKind.UX_STRATEGY, "u2", "Navigation pattern: persistent header with clear categories", 0.9, "navigation", "nav", "menu", "convention"),
        signal(ProvenanceKind.UX_STRATEGY, "u3", "Product page leads with the add-to-cart decision", 0.9, "product", "page", "cta", "conversion", "trust"),
        signal(ProvenanceKind.UX_STRATEGY, "u4", "Collection page supports browsing and comparison", 0.9, "collection", "page", "cta", "filter"),
        signal(ProvenanceKind.UX_STRATEGY, "u5", "Homepage orients and routes to collections", 0.9, "homepage", "page", "cta"),
        signal(ProvenanceKind.UX_STRATEGY, "u6", "Cart page reassures before checkout", 0.9, "cart", "page", "cta", "trust"),
        signal(ProvenanceKind.UX_STRATEGY, "u7", "Checkout minimises fields and friction", 0.9, "checkout", "page", "form", "conversion"),
        signal(ProvenanceKind.UX_STRATEGY, "u8", "Search returns relevant results with facets", 0.9, "search", "page", "filter", "sort"),
        signal(ProvenanceKind.UX_STRATEGY, "u9", "Account gives order history and control", 0.9, "account", "page"),
        signal(ProvenanceKind.PSYCHOLOGY, "p1", "Reviews reduce anxiety at consideration", 0.9, "trust", "review", "consideration", "conversion", "product"),
        signal(ProvenanceKind.PSYCHOLOGY, "p2", "Cost shock and hidden fees drive checkout drop-off", 0.9, "checkout", "objection", "trust", "form"),
        signal(ProvenanceKind.BRAND_STRATEGY, "br1", "The brand voice is elegant and restrained", 0.85, "tone", "brand"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Increase conversion and average order value", 0.9, "conversion", "aov", "business", "revenue", "positioning"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Faceted navigation improves large-catalog findability", 0.85, "navigation", "taxonomy", "filter", "breadcrumb"),
        signal(ProvenanceKind.KNOWLEDGE, "k2", "Cross-sell and related products lift AOV on PDPs", 0.85, "product", "cross-sell", "related", "aov"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        pages: tuple[PageType, ...] | None = None,
        catalog_scale: str = "large",
        has_blog: bool = False,
        has_wishlist: bool = False,
        market: str = "premium",
    ) -> IARequest:
        brief = (
            IABrief(product_category=product_category, pages=pages, catalog_scale=catalog_scale,
                    has_blog=has_blog, has_wishlist=has_wishlist)
            if pages is not None
            else IABrief(product_category=product_category, catalog_scale=catalog_scale,
                         has_blog=has_blog, has_wishlist=has_wishlist)
        )
        return IARequest(
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
        return build_in_memory_environment(
            ux=InMemoryUXInput(buckets[ProvenanceKind.UX_STRATEGY]),
            psychology=InMemoryPsychologyInput(buckets[ProvenanceKind.PSYCHOLOGY]),
            brand=InMemoryBrandInput(buckets[ProvenanceKind.BRAND_STRATEGY]),
            business_strategy=InMemoryBusinessStrategyInput(buckets[ProvenanceKind.BUSINESS_STRATEGY]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[ProvenanceKind.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[ProvenanceKind.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[ProvenanceKind.COMPETITOR]),
            reasoning=InMemoryReasoning(buckets[ProvenanceKind.REASONING]),
            clock=FixedClock(),
        )

    return _make
