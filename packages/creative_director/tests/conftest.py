"""Shared fixtures for the Creative Director Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from creative_director.application.contracts import RawSignal
from creative_director.application.ports.clock import Clock
from creative_director.application.request import ReviewRequest
from creative_director.domain.context.context import ProjectContext, ReviewSubject
from creative_director.domain.policy.policy import ReviewPolicy
from creative_director.domain.shared.value_objects import (
    ProvenanceKind,
    ReviewMode,
    ReviewProfileKind,
    SubjectKind,
)
from creative_director.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryReasoning,
    InMemoryResearchInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from creative_director.infrastructure.adapters.profiles import profile_for
from creative_director.infrastructure.container import build_in_memory_environment

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
def strong_signals() -> list[RawSignal]:
    """A rich, well-grounded subject that should score high and be approved."""
    P = ProvenanceKind
    return [
        signal(P.WIREFRAME, "w1", "Product page leads with gallery, buy box, add to cart", 0.9, "product", "conversion", "cta", "buy", "component", "structure", "section"),
        signal(P.WIREFRAME, "w2", "Trust badges, reviews and guarantees at the point of decision", 0.9, "trust", "review", "guarantee", "badge", "social"),
        signal(P.WIREFRAME, "w3", "Checkout minimizes fields; accessibility and performance attached", 0.9, "checkout", "accessibility", "wcag", "performance", "lazy", "mobile", "responsive"),
        signal(P.WIREFRAME, "w4", "Consistent components map to Shopify and Magento theme sections", 0.9, "component", "shopify", "magento", "theme", "scalability", "maintainability", "consistency", "spacing", "layout", "hierarchy"),
        signal(P.INFORMATION_ARCHITECTURE, "ia1", "Clear section priority and hierarchy", 0.88, "hierarchy", "priority", "structure", "section"),
        signal(P.UX_STRATEGY, "ux1", "Primary goal complete purchase; clear navigation flow", 0.9, "ux", "goal", "navigation", "flow", "user"),
        signal(P.BUSINESS_STRATEGY, "b1", "Premium positioning; increase conversion and AOV", 0.9, "business", "positioning", "conversion", "revenue", "aov"),
        signal(P.BRAND_STRATEGY, "br1", "Elegant restrained premium brand voice and typography", 0.85, "brand", "tone", "voice", "typography", "heading"),
        signal(P.PSYCHOLOGY, "p1", "Reviews reduce anxiety; objections resolved with guarantees", 0.9, "trust", "objection", "anxiety", "emotion", "confidence"),
        signal(P.KNOWLEDGE, "k1", "Accessibility, performance, spacing and component patterns", 0.85, "accessibility", "wcag", "performance", "spacing", "layout", "component", "pattern"),
        signal(P.RESEARCH, "r1", "Shoppers rely on imagery and reviews before buying", 0.8, "review", "trust"),
        signal(P.COMPETITOR, "c1", "Competitors lead PDPs with gallery and buy box", 0.8, "product", "conversion"),
        signal(P.REASONING, "rsn1", "Trust belongs adjacent to the primary CTA", 0.8, "trust", "conversion"),
    ]


@pytest.fixture
def weak_signals() -> list[RawSignal]:
    """A generic, purpose-free subject (the AI/Dribbble tell) that must be rejected."""
    return [
        signal(ProvenanceKind.WIREFRAME, "w1", "Hero, features and footer layout", 0.9, "hero", "features", "footer", "layout"),
    ]


@pytest.fixture
def subject() -> ReviewSubject:
    return ReviewSubject(
        kind=SubjectKind.WIREFRAME_PLAN, reference="wf-plan-1",
        label="Wireframe plan", phase="wireframe",
    )


@pytest.fixture
def request_factory(subject):
    def _make(*, profile: ReviewProfileKind = ReviewProfileKind.STARTUP,
              mode: ReviewMode = ReviewMode.AUTOMATIC, threshold=None) -> ReviewRequest:
        return ReviewRequest(
            subject=subject,
            policy=ReviewPolicy(profile=profile_for(profile), mode=mode, threshold_override=threshold),
            project=ProjectContext(project_id="proj-x", platform="shopify_plus", market="premium"),
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
            knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[P.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[P.COMPETITOR]),
            reasoning=InMemoryReasoning(buckets[P.REASONING]),
            clock=FixedClock(),
        )

    return _make
