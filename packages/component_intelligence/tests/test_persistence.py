"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced specification is stored as its codec document and reconstructed (re-validated)
on load, identical in content — components, compatibility, rules, and both graphs — and that
lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from component_intelligence.application.commands import BuildComposition
from component_intelligence.domain.shared.ids import ComponentSpecId, ComponentSpecLineageId
from component_intelligence.domain.shared.value_objects import ProvenanceKind
from component_intelligence.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryWireframeInput,
)
from component_intelligence.infrastructure.persistence.wiring import (
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

    P = ProvenanceKind
    env = build_sqlalchemy_environment(
        sf,
        wireframe=InMemoryWireframeInput(bucket(P.WIREFRAME)),
        business_strategy=InMemoryBusinessStrategyInput(bucket(P.BUSINESS_STRATEGY)),
        psychology=InMemoryPsychologyInput(bucket(P.PSYCHOLOGY)),
        creative_director=InMemoryCreativeDirectorInput(bucket(P.CREATIVE_DIRECTOR)),
        design_language=InMemoryDesignLanguageInput(bucket(P.DESIGN_LANGUAGE)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(P.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_specification_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.compose(BuildComposition(request=request_factory()))
    sid = ComponentSpecId.from_string(view.spec_id)

    reloaded = await sql_env.facade.get(sid)  # decoded + re-validated from the DB
    assert reloaded.spec_id == view.spec_id
    assert reloaded.version == view.version
    assert reloaded.components == view.components
    assert reloaded.compatibility == view.compatibility
    assert reloaded.placement_rules == view.placement_rules
    assert reloaded.graphs == view.graphs
    assert reloaded.quality.overall_score == view.quality.overall_score


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = ComponentSpecLineageId.new()
    await sql_env.facade.compose(BuildComposition(request=request_factory(), lineage_id=lineage))
    await sql_env.facade.compose(BuildComposition(request=request_factory(), lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [s.version for s in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
