"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced plan is stored as its codec document and reconstructed (re-validated) on
load, identical in content — pages, sections, blocks, components, approvals, and all six
graphs — and that lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from wireframe.application.commands import BuildWireframePlan
from wireframe.domain.shared.ids import WireframePlanId, WireframePlanLineageId
from wireframe.domain.shared.value_objects import ProvenanceKind
from wireframe.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
)
from wireframe.infrastructure.persistence.wiring import (
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
        ia=InMemoryIAInput(bucket(ProvenanceKind.INFORMATION_ARCHITECTURE)),
        ux=InMemoryUXInput(bucket(ProvenanceKind.UX_STRATEGY)),
        business_strategy=InMemoryBusinessStrategyInput(bucket(ProvenanceKind.BUSINESS_STRATEGY)),
        psychology=InMemoryPsychologyInput(bucket(ProvenanceKind.PSYCHOLOGY)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(ProvenanceKind.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_plan_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.plan(BuildWireframePlan(request=request_factory()))
    rid = WireframePlanId.from_string(view.plan_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.plan_id == view.plan_id
    assert reloaded.version == view.version
    assert reloaded.quality.overall_score == view.quality.overall_score
    assert reloaded.evidence_count == view.evidence_count
    assert reloaded.section_count == view.section_count
    assert reloaded.pages == view.pages
    assert reloaded.graphs == view.graphs
    assert reloaded.approval_plan == view.approval_plan


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = WireframePlanLineageId.new()
    req = request_factory()
    await sql_env.facade.plan(BuildWireframePlan(request=req, lineage_id=lineage))
    await sql_env.facade.plan(BuildWireframePlan(request=req, lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
