"""Shared fixtures for the Brand Strategy Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from brand.application.contracts import RawSignal
from brand.application.ports.clock import Clock
from brand.application.request import BrandRequest
from brand.domain.context.context import BrandBrief, ProjectContext
from brand.domain.shared.value_objects import ProvenanceKind
from brand.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryKnowledgeAdvisor,
    InMemoryReasoning,
    InMemoryResearchInput,
)
from brand.infrastructure.container import build_in_memory_environment

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
    return [
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Position as premium: trusted value customers commit to", 0.9, "premium", "positioning", "brand"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s2", "Evoke trust and confidence at consideration", 0.85, "trust", "emotion", "feel"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s3", "Reviews and guarantees are required trust signals", 0.85, "trust", "review", "guarantee"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Editorial serif conveys premium credibility", 0.8, "typography", "premium", "brand"),
        signal(ProvenanceKind.KNOWLEDGE, "k2", "Restrained colour with a single accent signals quality", 0.8, "color", "minimal", "visual"),
        signal(ProvenanceKind.KNOWLEDGE, "k3", "Consistent voice builds brand trust", 0.8, "voice", "consistency", "brand"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        name: str = "Aesop",
        industry: str = "beauty skincare",
        market: str = "premium",
        descriptors: tuple[str, ...] = ("premium", "crafted", "minimal"),
        category_hint=None,
    ) -> BrandRequest:
        return BrandRequest(
            brief=BrandBrief(
                name=name, industry=industry, maturity="established",
                descriptors=descriptors, category_hint=category_hint,
            ),
            project=ProjectContext(
                project_id="proj-aesop", platform="shopify_plus", market=market
            ),
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
            business_strategy=InMemoryBusinessStrategyInput(buckets[ProvenanceKind.BUSINESS_STRATEGY]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[ProvenanceKind.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[ProvenanceKind.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[ProvenanceKind.COMPETITOR]),
            reasoning=InMemoryReasoning(buckets[ProvenanceKind.REASONING]),
            clock=FixedClock(),
        )

    return _make
