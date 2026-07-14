"""Shared fixtures for the Design Language Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from design_language.application.contracts import RawSignal
from design_language.application.ports.clock import Clock
from design_language.application.request import DesignLanguageRequest
from design_language.domain.context.context import DesignBrief, ProjectContext
from design_language.domain.shared.value_objects import IndustryPreset, LanguageArchetype, ProvenanceKind
from design_language.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryCreativeDirectorInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryResearchInput,
)
from design_language.infrastructure.container import build_in_memory_environment

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
    """A rich, cross-provenance signal set covering the language's grounding needs."""
    P = ProvenanceKind
    return [
        signal(P.BRAND_STRATEGY, "br1", "Elegant, restrained premium apothecary brand voice", 0.9, "brand", "tone", "identity", "voice", "premium"),
        signal(P.BUSINESS_STRATEGY, "b1", "Premium positioning; conversion through considered restraint", 0.9, "business", "positioning", "conversion", "revenue"),
        signal(P.PSYCHOLOGY, "p1", "Calm and reviews reduce purchase anxiety at consideration", 0.9, "trust", "emotion", "anxiety", "confidence", "calm"),
        signal(P.CREATIVE_DIRECTOR, "cd1", "Approved premium quality direction; reject generic looks", 0.9, "quality", "approved", "review", "premium", "restraint"),
        signal(P.KNOWLEDGE, "k1", "Modular spacing, single type ratio, restraint and timelessness", 0.85, "spacing", "type", "grid", "system", "restraint", "premium", "timeless"),
        signal(P.RESEARCH, "r1", "Shoppers respond to considered, uncluttered premium visuals", 0.8, "premium", "restraint"),
        signal(P.COMPETITOR, "c1", "Category leaders use restrained, editorial visual systems", 0.8, "premium", "editorial", "restraint"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        industry: IndustryPreset = IndustryPreset.BEAUTY,
        tier: str = "premium",
        preferred_archetype: LanguageArchetype | None = None,
        product_category: str = "skincare",
    ) -> DesignLanguageRequest:
        return DesignLanguageRequest(
            brief=DesignBrief(industry=industry, tier=tier, product_category=product_category,
                              preferred_archetype=preferred_archetype),
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
            business_strategy=InMemoryBusinessStrategyInput(buckets[P.BUSINESS_STRATEGY]),
            brand=InMemoryBrandInput(buckets[P.BRAND_STRATEGY]),
            psychology=InMemoryPsychologyInput(buckets[P.PSYCHOLOGY]),
            creative_director=InMemoryCreativeDirectorInput(buckets[P.CREATIVE_DIRECTOR]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[P.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[P.COMPETITOR]),
            clock=FixedClock(),
        )

    return _make
