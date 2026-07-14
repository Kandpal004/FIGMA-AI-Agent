"""Shared fixtures for the Competitor Intelligence Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from competitive.application.ports.knowledge_advisor import AdvisedPrinciple
from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.observation import Observation, ObservationSet
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.ids import CompetitorId, ObservationId
from competitive.domain.shared.value_objects import (
    CompetitorDimension as Dim, Confidence, ObservationSource, Score)
from competitive.infrastructure.container import build_in_memory_environment
from competitive.infrastructure.inmemory import Clock, InMemoryDataSource, InMemoryKnowledgeAdvisor


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)


def _p(kid: str, category: str, statement: str) -> AdvisedPrinciple:
    return AdvisedPrinciple(kid, f"{kid}-v1", category, f"{category} bp", statement, "NNG", 0.85, "rel")


@pytest.fixture
def competitors() -> tuple[Competitor, ...]:
    c1, c2, c3 = CompetitorId.new(), CompetitorId.new(), CompetitorId.new()
    return (
        Competitor(id=c1, name="Aesop", industry="beauty", market="premium"),
        Competitor(id=c2, name="Glossier", industry="beauty", market="premium"),
        Competitor(id=c3, name="Sephora", industry="beauty", market="mass"),
    )


@pytest.fixture
def observations(competitors) -> ObservationSet:
    c1, c2, c3 = (c.id for c in competitors)

    def o(cid, dim, finding, strength):
        return Observation(id=ObservationId.new(), competitor_id=cid, dimension=dim, finding=finding,
                           source=ObservationSource.MANUAL, confidence=Confidence.of(0.9), strength=Score.of(strength))

    return ObservationSet.of([
        o(c1, Dim.CONVERSION_PATTERNS, "Prominent CTA", 90), o(c2, Dim.CONVERSION_PATTERNS, "Sticky ATC", 82),
        o(c3, Dim.CONVERSION_PATTERNS, "One-click", 92), o(c1, Dim.TYPOGRAPHY, "Editorial serif", 88),
        o(c2, Dim.TYPOGRAPHY, "Clean sans", 78), o(c3, Dim.TYPOGRAPHY, "System font", 40),
        o(c1, Dim.TRUST_STRATEGY, "Reviews", 80), o(c2, Dim.TRUST_STRATEGY, "UGC", 75),
    ])


@pytest.fixture
def full_advisor() -> InMemoryKnowledgeAdvisor:
    return InMemoryKnowledgeAdvisor({
        Dim.CONVERSION_PATTERNS: [_p("kc", "conversion_optimization", "One high-contrast CTA lifts conversion.")],
        Dim.TYPOGRAPHY: [_p("kt", "typography", "High-contrast serif conveys editorial trust.")],
        Dim.TRUST_STRATEGY: [_p("ktr", "conversion_optimization", "Visible reviews reduce anxiety.")],
    })


@pytest.fixture
def brief(competitors) -> CompetitiveBrief:
    return CompetitiveBrief.build(
        "beauty", market="premium", country="US", business_goals=["grow AOV"], client_name="Acme",
        client_baseline={Dim.CONVERSION_PATTERNS: Score.of(45), Dim.TYPOGRAPHY: Score.of(50),
                         Dim.TRUST_STRATEGY: Score.of(60)},
        competitors=list(competitors))


@pytest.fixture
def env_factory(observations):
    def _make(advisor, *, reasoning=None):
        return build_in_memory_environment(
            data_source=InMemoryDataSource(observations), advisor=advisor,
            reasoning=reasoning, clock=FixedClock())

    return _make
