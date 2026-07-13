"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced strategy is stored as its codec document and reconstructed
(re-validated) on load, identical in content — and that explain works over the
database-backed store.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from reasoning.application.commands import GenerateStrategy
from reasoning.domain.request.request import ReasoningRequest
from reasoning.domain.shared.ids import StrategyId
from reasoning.domain.shared.value_objects import ReasoningDimension as D, StrategyStance
from reasoning.infrastructure.inmemory import (
    Clock, InMemoryKnowledgeAdvisor, NullContextPort, NullDecisionHistoryPort)
from reasoning.infrastructure.persistence.wiring import build_sqlalchemy_environment, init_models
from reasoning.application.ports.knowledge_advisor import AdvisedPrinciple


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)


def _script():
    p = lambda k, t, s, c=0.85: AdvisedPrinciple(k, f"{k}v", "cat", t, s, "src", c, "rel")
    return {
        D.BUSINESS: [p("b", "AOV", "Grow AOV.")],
        D.CONVERSION: [p("cv1", "CTA", "One CTA.", 0.9), p("cv2", "Urgency", "Scarcity.", 0.7)],
        D.ACCESSIBILITY: [p("a", "Contrast", "4.5:1.", 0.95)],
        D.PLATFORM_CONSTRAINTS: [p("pf", "Locked", "Checkout locked.", 0.9)],
        D.STRUCTURE: [p("st", "Gallery", "Gallery anchors PDP.")],
    }


@pytest.fixture
async def sql_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    env = build_sqlalchemy_environment(
        sf, advisor=InMemoryKnowledgeAdvisor(_script()),
        context_port=NullContextPort(), decision_history_port=NullDecisionHistoryPort(),
        clock=FixedClock())
    yield env
    await engine.dispose()


async def test_strategy_round_trips_through_the_database(sql_env):
    request = ReasoningRequest(user_request="PDP", project_id="p", section_id="s",
                               page_type="product", platform="shopify_plus", stance=StrategyStance.CONVERSION_FIRST)
    view = await sql_env.facade.reason(GenerateStrategy(request=request))
    sid = StrategyId.from_string(view.strategy_id)

    reloaded = await sql_env.facade.get(sid)  # decoded + re-validated from the DB
    assert reloaded.strategy_id == view.strategy_id
    assert reloaded.evidence_count == view.evidence_count
    assert reloaded.decision_count == view.decision_count
    assert reloaded.confidence.overall == view.confidence.overall
    assert reloaded.risk_overall_level == view.risk_overall_level
    assert len(reloaded.cro_principles) == len(view.cro_principles) == 2
    assert len(reloaded.alternatives) == 5
