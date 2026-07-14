"""Shared fixtures for the UX Strategy Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ux.application.contracts import RawSignal
from ux.application.ports.clock import Clock
from ux.application.request import UXRequest
from ux.domain.context.context import ProjectContext, UXBrief
from ux.domain.shared.value_objects import DeviceContext, ProvenanceKind
from ux.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryCompetitorInsight,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryReasoning,
    InMemoryResearchInput,
)
from ux.infrastructure.container import build_in_memory_environment

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
        signal(ProvenanceKind.PSYCHOLOGY, "p1", "Customers feel anxiety at consideration; reviews reduce it", 0.9, "trust", "anxiety", "review", "consideration"),
        signal(ProvenanceKind.PSYCHOLOGY, "p2", "Checkout friction and cost shock drive drop-off", 0.9, "checkout", "cost", "conversion", "form"),
        signal(ProvenanceKind.BRAND_STRATEGY, "b1", "The brand voice is elegant; interactions express restraint", 0.85, "tone", "brand", "interaction"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Increase conversion and AOV; premium value", 0.9, "conversion", "aov", "value", "business"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Baymard: fewer checkout fields lifts completion", 0.85, "checkout", "baymard", "form"),
        signal(ProvenanceKind.KNOWLEDGE, "k2", "WCAG AA contrast and focus order required", 0.85, "accessibility", "wcag"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        pages=None,
        device: DeviceContext = DeviceContext.RESPONSIVE,
        market: str = "premium",
    ) -> UXRequest:
        brief = (
            UXBrief(product_category=product_category, pages=pages, device_priority=device)
            if pages is not None
            else UXBrief(product_category=product_category, device_priority=device)
        )
        return UXRequest(
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
