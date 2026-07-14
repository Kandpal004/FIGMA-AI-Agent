"""Shared fixtures for the Business Strategy Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from strategy.application.contracts import RawInsight
from strategy.application.ports.clock import Clock
from strategy.application.request import StrategyRequest
from strategy.domain.context.context import BrandContext, GoalContext, ProjectContext
from strategy.domain.shared.value_objects import ProvenanceKind
from strategy.infrastructure.adapters.inmemory_inputs import (
    InMemoryCompetitorInsight,
    InMemoryKnowledgeAdvisor,
    InMemoryReasoning,
    InMemoryResearchInput,
)
from strategy.infrastructure.container import build_in_memory_environment

FIXED_NOW = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return FIXED_NOW


def insight(
    provenance: ProvenanceKind, ref: str, claim: str, confidence: float, *tags: str
) -> RawInsight:
    return RawInsight(
        provenance=provenance,
        external_ref=ref,
        claim=claim,
        confidence=confidence,
        source_name=provenance.value,
        tags=tags,
    )


@pytest.fixture
def insights() -> list[RawInsight]:
    return [
        insight(ProvenanceKind.RESEARCH, "r1", "Customers rely on reviews and trust before buying", 0.9, "trust", "review"),
        insight(ProvenanceKind.KNOWLEDGE, "k1", "One high-contrast CTA and clear value lifts conversion", 0.85, "conversion", "value"),
        insight(ProvenanceKind.COMPETITOR, "c1", "Premium competitors lead with editorial trust and guarantees", 0.8, "premium", "guarantee", "trust"),
        insight(ProvenanceKind.REASONING, "x1", "A free shipping threshold raises average order value", 0.7, "aov", "shipping"),
        insight(ProvenanceKind.KNOWLEDGE, "k2", "Loyalty programs improve retention", 0.8, "retention", "loyalty"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        project_id: str = "proj-acme",
        market: str = "premium",
        descriptors: tuple[str, ...] = ("premium", "crafted"),
        business_goals: tuple[str, ...] = ("Increase conversion rate", "Grow retention"),
    ) -> StrategyRequest:
        return StrategyRequest(
            brand=BrandContext(
                name="Acme", industry="beauty", maturity="growth", descriptors=descriptors
            ),
            project=ProjectContext(
                project_id=project_id, platform="shopify_plus", market=market
            ),
            goals=GoalContext(business_goals=business_goals, user_goals=("Buy with confidence",)),
        )

    return _make


@pytest.fixture
def env_factory():
    """Build an in-memory environment whose input ports return the given insights."""

    def _make(insights_list=(), *, split=True):
        research_i, knowledge_i, competitor_i, reasoning_i = [], [], [], []
        for ins in insights_list:
            {
                ProvenanceKind.RESEARCH: research_i,
                ProvenanceKind.KNOWLEDGE: knowledge_i,
                ProvenanceKind.COMPETITOR: competitor_i,
                ProvenanceKind.REASONING: reasoning_i,
            }.get(ins.provenance, research_i).append(ins)
        return build_in_memory_environment(
            research=InMemoryResearchInput(research_i),
            knowledge=InMemoryKnowledgeAdvisor(knowledge_i),
            competitor=InMemoryCompetitorInsight(competitor_i),
            reasoning=InMemoryReasoning(reasoning_i),
            clock=FixedClock(),
        )

    return _make
