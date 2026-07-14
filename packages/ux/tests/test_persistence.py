"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced report is stored as its codec document and reconstructed (re-validated)
on load, identical in content, and that versioning works in the DB.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ux.application.commands import BuildUXStrategy
from ux.domain.shared.ids import UXReportId, UXReportLineageId
from ux.domain.shared.value_objects import ProvenanceKind
from ux.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
)
from ux.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import FixedClock, signal


def _signals():
    return [
        signal(ProvenanceKind.PSYCHOLOGY, "p1", "Reviews reduce anxiety; checkout friction drives dropoff", 0.9, "trust", "checkout", "review"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Increase conversion and AOV", 0.9, "conversion", "aov", "business"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Baymard checkout patterns lift completion", 0.85, "checkout", "baymard"),
    ]


@pytest.fixture
async def sql_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    ins = _signals()
    env = build_sqlalchemy_environment(
        sf,
        psychology=InMemoryPsychologyInput([i for i in ins if i.provenance is ProvenanceKind.PSYCHOLOGY]),
        business_strategy=InMemoryBusinessStrategyInput([i for i in ins if i.provenance is ProvenanceKind.BUSINESS_STRATEGY]),
        knowledge=InMemoryKnowledgeAdvisor([i for i in ins if i.provenance is ProvenanceKind.KNOWLEDGE]),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.build(BuildUXStrategy(request=request_factory()))
    rid = UXReportId.from_string(view.report_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.version == view.version
    assert reloaded.quality.overall_score == view.quality.overall_score
    assert reloaded.evidence_count == view.evidence_count
    assert reloaded.pages == view.pages
    assert reloaded.journeys == view.journeys
    assert reloaded.graphs == view.graphs
    assert reloaded.laws == view.laws
    assert reloaded.flows == view.flows


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = UXReportLineageId.new()
    req = request_factory()
    await sql_env.facade.build(BuildUXStrategy(request=req, lineage_id=lineage))
    await sql_env.facade.build(BuildUXStrategy(request=req, lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
