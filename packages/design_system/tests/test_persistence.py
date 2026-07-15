"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced specification is stored as its codec document and reconstructed (re-validated)
on load, identical in content — tokens, scales, systems, components, themes, constraints, and all
six graphs — and that lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from design_system.application.commands import BuildDesignSystem
from design_system.domain.shared.ids import (
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
)
from design_system.domain.shared.value_objects import ProvenanceKind
from design_system.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryComponentIntelligenceInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from design_system.infrastructure.persistence.wiring import (
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
        design_language=InMemoryDesignLanguageInput(bucket(P.DESIGN_LANGUAGE)),
        component_intelligence=InMemoryComponentIntelligenceInput(bucket(P.COMPONENT_INTELLIGENCE)),
        creative_director=InMemoryCreativeDirectorInput(bucket(P.CREATIVE_DIRECTOR)),
        business_strategy=InMemoryBusinessStrategyInput(bucket(P.BUSINESS_STRATEGY)),
        brand=InMemoryBrandInput(bucket(P.BRAND_STRATEGY)),
        psychology=InMemoryPsychologyInput(bucket(P.PSYCHOLOGY)),
        ux=InMemoryUXInput(bucket(P.UX_STRATEGY)),
        ia=InMemoryIAInput(bucket(P.INFORMATION_ARCHITECTURE)),
        wireframe=InMemoryWireframeInput(bucket(P.WIREFRAME)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(P.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_specification_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.build(BuildDesignSystem(request=request_factory()))
    sid = DesignSystemSpecId.from_string(view.spec_id)

    reloaded = await sql_env.facade.get(sid)  # decoded + re-validated from the DB
    assert reloaded.spec_id == view.spec_id
    assert reloaded.version == view.version
    assert reloaded.tokens == view.tokens
    assert reloaded.scales == view.scales
    assert reloaded.systems == view.systems
    assert reloaded.states == view.states
    assert reloaded.components == view.components
    assert reloaded.themes == view.themes
    assert reloaded.localization == view.localization
    assert reloaded.constraints == view.constraints
    assert reloaded.graphs == view.graphs
    assert reloaded.quality.overall_score == view.quality.overall_score


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = DesignSystemSpecLineageId.new()
    await sql_env.facade.build(BuildDesignSystem(request=request_factory(), lineage_id=lineage))
    await sql_env.facade.build(BuildDesignSystem(request=request_factory(), lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [s.version for s in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
