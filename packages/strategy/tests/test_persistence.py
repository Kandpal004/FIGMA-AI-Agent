"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced report is stored as its codec document and reconstructed
(re-validated) on load, identical in content, and that versioning works in the DB.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from strategy.application.commands import BuildStrategy
from strategy.domain.shared.ids import StrategyReportId, StrategyReportLineageId
from strategy.domain.shared.value_objects import ProvenanceKind
from strategy.infrastructure.adapters.inmemory_inputs import (
    InMemoryCompetitorInsight,
    InMemoryKnowledgeAdvisor,
    InMemoryResearchInput,
)
from strategy.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import FixedClock, insight


def _insights():
    return [
        insight(ProvenanceKind.RESEARCH, "r1", "Reviews and trust drive purchase confidence", 0.9, "trust"),
        insight(ProvenanceKind.KNOWLEDGE, "k1", "Clear value and a strong CTA lift conversion", 0.85, "conversion"),
        insight(ProvenanceKind.COMPETITOR, "c1", "Premium rivals lead with guarantees", 0.8, "premium"),
    ]


@pytest.fixture
async def sql_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    ins = _insights()
    env = build_sqlalchemy_environment(
        sf,
        research=InMemoryResearchInput([i for i in ins if i.provenance is ProvenanceKind.RESEARCH]),
        knowledge=InMemoryKnowledgeAdvisor([i for i in ins if i.provenance is ProvenanceKind.KNOWLEDGE]),
        competitor=InMemoryCompetitorInsight([i for i in ins if i.provenance is ProvenanceKind.COMPETITOR]),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.build(BuildStrategy(request=request_factory()))
    rid = StrategyReportId.from_string(view.report_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.version == view.version
    assert reloaded.tier == view.tier
    assert reloaded.quality.overall_score == view.quality.overall_score
    assert len(reloaded.decisions) == len(view.decisions)
    assert reloaded.evidence_count == view.evidence_count
    assert len(reloaded.priority_matrix) == len(view.priority_matrix)
    assert reloaded.positioning.statement == view.positioning.statement


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = StrategyReportLineageId.new()
    req = request_factory()
    await sql_env.facade.build(BuildStrategy(request=req, lineage_id=lineage))
    await sql_env.facade.build(BuildStrategy(request=req, lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
