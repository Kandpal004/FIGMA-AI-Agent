"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced report is stored as its codec document and reconstructed
(re-validated) on load, identical in content.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from competitive.application.commands import AnalyzeCompetitors
from competitive.domain.shared.ids import ReportId
from competitive.infrastructure.inmemory import Clock, InMemoryDataSource
from competitive.infrastructure.persistence.wiring import build_sqlalchemy_environment, init_models


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
async def sql_env(observations, full_advisor):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    env = build_sqlalchemy_environment(
        sf, data_source=InMemoryDataSource(observations), advisor=full_advisor, clock=FixedClock())
    yield env
    await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env, brief):
    view = await sql_env.facade.analyze(AnalyzeCompetitors(brief=brief))
    rid = ReportId.from_string(view.report_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.confidence == view.confidence
    assert len(reloaded.recommendations) == len(view.recommendations)
    assert len(reloaded.evidence) == len(view.evidence)
    assert reloaded.risk_overall_level == view.risk_overall_level
    assert [p.name for p in reloaded.all_patterns] == [p.name for p in view.all_patterns]
    assert reloaded.overall_gap_index == view.overall_gap_index
