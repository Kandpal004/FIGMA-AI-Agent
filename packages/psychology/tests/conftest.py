"""Shared fixtures for the Customer Psychology Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from psychology.application.contracts import RawSignal
from psychology.application.ports.clock import Clock
from psychology.application.request import PsychologyRequest
from psychology.domain.context.context import ProjectContext, PsychologyBrief
from psychology.domain.shared.value_objects import ProvenanceKind
from psychology.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryKnowledgeAdvisor,
    InMemoryReasoning,
    InMemoryResearchInput,
)
from psychology.infrastructure.container import build_in_memory_environment

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
        signal(ProvenanceKind.BRAND_STRATEGY, "b1", "Evoke trust and confidence; caregiver archetype", 0.9, "trust", "emotion", "brand"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Position as premium trusted value; reviews and guarantees required", 0.9, "premium", "trust", "review", "guarantee"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Social proof reduces anxiety at consideration", 0.85, "social", "proof", "anxiety"),
        signal(ProvenanceKind.KNOWLEDGE, "k2", "Loss aversion: a guarantee reframes risk", 0.8, "guarantee", "risk", "loss"),
        signal(ProvenanceKind.RESEARCH, "r1", "Customers read reviews before deciding", 0.85, "review", "behavior", "trust"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        price_band: str = "premium",
        purchase_type: str = "considered",
        purchase_risk: str = "high",
        market: str = "premium",
        descriptors: tuple[str, ...] = (),
    ) -> PsychologyRequest:
        return PsychologyRequest(
            brief=PsychologyBrief(
                product_category=product_category, price_band=price_band,
                purchase_type=purchase_type, purchase_risk=purchase_risk, descriptors=descriptors,
            ),
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
            brand=InMemoryBrandInput(buckets[ProvenanceKind.BRAND_STRATEGY]),
            business_strategy=InMemoryBusinessStrategyInput(buckets[ProvenanceKind.BUSINESS_STRATEGY]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[ProvenanceKind.KNOWLEDGE]),
            research=InMemoryResearchInput(buckets[ProvenanceKind.RESEARCH]),
            competitor=InMemoryCompetitorInsight(buckets[ProvenanceKind.COMPETITOR]),
            reasoning=InMemoryReasoning(buckets[ProvenanceKind.REASONING]),
            clock=FixedClock(),
        )

    return _make
