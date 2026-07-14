"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced IA report is stored as its codec document and reconstructed (re-validated)
on load, identical in content — site map, navigation, relationships, discovery, and all six
graphs — and that lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ia.application.commands import BuildIA
from ia.domain.shared.ids import IAReportId, IAReportLineageId
from ia.domain.shared.value_objects import ProvenanceKind
from ia.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
)
from ia.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import FixedClock


@pytest.fixture
async def sql_env(signals):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)

    def bucket(kind: ProvenanceKind):
        return [s for s in signals if s.provenance is kind]

    env = build_sqlalchemy_environment(
        sf,
        ux=InMemoryUXInput(bucket(ProvenanceKind.UX_STRATEGY)),
        psychology=InMemoryPsychologyInput(bucket(ProvenanceKind.PSYCHOLOGY)),
        brand=InMemoryBrandInput(bucket(ProvenanceKind.BRAND_STRATEGY)),
        business_strategy=InMemoryBusinessStrategyInput(bucket(ProvenanceKind.BUSINESS_STRATEGY)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(ProvenanceKind.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.build(BuildIA(request=request_factory()))
    rid = IAReportId.from_string(view.report_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.version == view.version
    assert reloaded.quality.overall_score == view.quality.overall_score
    assert reloaded.evidence_count == view.evidence_count
    assert reloaded.required_pages == view.required_pages
    assert reloaded.optional_pages == view.optional_pages
    assert reloaded.navigation == view.navigation
    assert reloaded.relationships == view.relationships
    assert reloaded.discovery == view.discovery
    assert reloaded.graphs == view.graphs


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = IAReportLineageId.new()
    req = request_factory()
    await sql_env.facade.build(BuildIA(request=req, lineage_id=lineage))
    await sql_env.facade.build(BuildIA(request=req, lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
