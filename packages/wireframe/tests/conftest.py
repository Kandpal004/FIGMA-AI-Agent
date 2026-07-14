"""Shared fixtures for the Wireframe Planning Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from wireframe.application.contracts import RawSignal
from wireframe.application.ports.clock import Clock
from wireframe.application.request import WireframeRequest
from wireframe.domain.context.context import ProjectContext, WireframeBrief
from wireframe.domain.shared.value_objects import PageType, ProvenanceKind
from wireframe.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryReasoning,
    InMemoryResearchInput,
    InMemoryUXInput,
)
from wireframe.infrastructure.container import build_in_memory_environment

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
    """A rich, cross-provenance signal set covering the plan's grounding needs."""
    out = [
        signal(ProvenanceKind.INFORMATION_ARCHITECTURE, "ia-nav", "Navigation and breadcrumbs structure wayfinding", 0.9, "navigation", "structure", "nav", "breadcrumb"),
        signal(ProvenanceKind.UX_STRATEGY, "ux-goal", "Primary user goal: complete a confident purchase", 0.9, "goal", "user", "conversion"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "biz-1", "Increase conversion and average order value", 0.9, "business", "conversion", "aov", "revenue", "positioning"),
        signal(ProvenanceKind.BRAND_STRATEGY, "brand-1", "Elegant, restrained premium brand voice", 0.85, "brand", "tone", "positioning"),
        signal(ProvenanceKind.PSYCHOLOGY, "psy-1", "Reviews and guarantees reduce anxiety and build trust", 0.9, "trust", "review", "objection", "confidence", "guarantee"),
        signal(ProvenanceKind.KNOWLEDGE, "know-1", "Component patterns, accessibility, and clear structure lift usability", 0.85, "component", "pattern", "accessibility", "structure", "navigation", "layout"),
        signal(ProvenanceKind.RESEARCH, "res-1", "Shoppers rely on imagery and reviews before buying", 0.8, "review", "content", "trust"),
        signal(ProvenanceKind.COMPETITOR, "comp-1", "Competitors lead PDPs with gallery and buy box", 0.8, "product", "structure", "conversion"),
        signal(ProvenanceKind.REASONING, "rsn-1", "Trust signals belong adjacent to the primary CTA", 0.8, "trust", "conversion", "structure"),
    ]
    # A per-page IA signal so every page's structure is IA-grounded.
    for pt in ("homepage", "collection", "product", "cart", "checkout", "search", "account", "blog", "landing"):
        out.append(signal(ProvenanceKind.INFORMATION_ARCHITECTURE, f"ia-{pt}", f"IA defines the {pt} page structure", 0.88, pt, "page", "section", "structure", "content", "navigation"))
    return out


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        pages: tuple[PageType, ...] | None = None,
        catalog_scale: str = "large",
        has_blog: bool = False,
        has_landing: bool = False,
        market: str = "premium",
    ) -> WireframeRequest:
        brief = (
            WireframeBrief(product_category=product_category, pages=pages, catalog_scale=catalog_scale,
                           has_blog=has_blog, has_landing=has_landing)
            if pages is not None
            else WireframeBrief(product_category=product_category, catalog_scale=catalog_scale,
                                has_blog=has_blog, has_landing=has_landing)
        )
        return WireframeRequest(
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
            ia=InMemoryIAInput(buckets[ProvenanceKind.INFORMATION_ARCHITECTURE]),
            ux=InMemoryUXInput(buckets[ProvenanceKind.UX_STRATEGY]),
            business_strategy=InMemoryBusinessStrategyInput(buckets[ProvenanceKind.BUSINESS_STRATEGY]),
            brand=InMemoryBrandInput(buckets[ProvenanceKind.BRAND_STRATEGY]),
            psychology=InMemoryPsychologyInput(buckets[ProvenanceKind.PSYCHOLOGY]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[ProvenanceKind.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[ProvenanceKind.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[ProvenanceKind.COMPETITOR]),
            reasoning=InMemoryReasoning(buckets[ProvenanceKind.REASONING]),
            clock=FixedClock(),
        )

    return _make
