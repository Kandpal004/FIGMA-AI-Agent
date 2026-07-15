"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced model is stored as its codec document and reconstructed (re-validated) on load,
identical in content — pages, collections, styles, component sets, mappings, and all five graphs —
and that lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from figma_design.application.commands import BuildFigmaDesign
from figma_design.domain.shared.ids import (
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
)
from figma_design.domain.shared.value_objects import ProvenanceKind
from figma_design.infrastructure.adapters.inmemory_inputs import (
    InMemoryComponentIntelligenceInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryDesignOrchestratorInput,
    InMemoryDesignSystemInput,
    InMemoryKnowledgeAdvisor,
)
from figma_design.infrastructure.persistence.wiring import (
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
        design_orchestrator=InMemoryDesignOrchestratorInput(bucket(P.DESIGN_ORCHESTRATOR)),
        design_system=InMemoryDesignSystemInput(bucket(P.DESIGN_SYSTEM)),
        component_intelligence=InMemoryComponentIntelligenceInput(bucket(P.COMPONENT_INTELLIGENCE)),
        design_language=InMemoryDesignLanguageInput(bucket(P.DESIGN_LANGUAGE)),
        creative_director=InMemoryCreativeDirectorInput(bucket(P.CREATIVE_DIRECTOR)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(P.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_model_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.compose(BuildFigmaDesign(request=request_factory()))
    mid = FigmaDesignModelId.from_string(view.model_id)

    reloaded = await sql_env.facade.get(mid)  # decoded + re-validated from the DB
    assert reloaded.model_id == view.model_id
    assert reloaded.version == view.version
    assert reloaded.pages == view.pages
    assert reloaded.collections == view.collections
    assert reloaded.styles == view.styles
    assert reloaded.component_sets == view.component_sets
    assert reloaded.token_mapping == view.token_mapping
    assert reloaded.variant_mapping == view.variant_mapping
    assert reloaded.graphs == view.graphs
    assert reloaded.source_refs == view.source_refs
    assert reloaded.quality.overall_score == view.quality.overall_score


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = FigmaDesignModelLineageId.new()
    await sql_env.facade.compose(BuildFigmaDesign(request=request_factory(), lineage_id=lineage))
    await sql_env.facade.compose(BuildFigmaDesign(request=request_factory(), lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [m.version for m in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
