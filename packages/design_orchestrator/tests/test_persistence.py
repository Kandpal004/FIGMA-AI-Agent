"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced plan is stored as its codec document and reconstructed (re-validated) on load,
identical in content — pages, tree, layout, mappings, both graphs, and the review plan — and that
lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from design_orchestrator.application.commands import BuildExecutionPlan
from design_orchestrator.domain.shared.ids import (
    DesignExecutionPlanId,
    DesignExecutionPlanLineageId,
)
from design_orchestrator.domain.shared.value_objects import ProvenanceKind
from design_orchestrator.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryComponentIntelligenceInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryDesignSystemInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from design_orchestrator.infrastructure.persistence.wiring import (
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
        design_system=InMemoryDesignSystemInput(bucket(P.DESIGN_SYSTEM)),
        component_intelligence=InMemoryComponentIntelligenceInput(bucket(P.COMPONENT_INTELLIGENCE)),
        wireframe=InMemoryWireframeInput(bucket(P.WIREFRAME)),
        creative_director=InMemoryCreativeDirectorInput(bucket(P.CREATIVE_DIRECTOR)),
        design_language=InMemoryDesignLanguageInput(bucket(P.DESIGN_LANGUAGE)),
        ia=InMemoryIAInput(bucket(P.INFORMATION_ARCHITECTURE)),
        ux=InMemoryUXInput(bucket(P.UX_STRATEGY)),
        psychology=InMemoryPsychologyInput(bucket(P.PSYCHOLOGY)),
        brand=InMemoryBrandInput(bucket(P.BRAND_STRATEGY)),
        business_strategy=InMemoryBusinessStrategyInput(bucket(P.BUSINESS_STRATEGY)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(P.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_plan_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    pid = DesignExecutionPlanId.from_string(view.plan_id)

    reloaded = await sql_env.facade.get(pid)  # decoded + re-validated from the DB
    assert reloaded.plan_id == view.plan_id
    assert reloaded.version == view.version
    assert reloaded.pages == view.pages
    assert reloaded.component_tree == view.component_tree
    assert reloaded.layout == view.layout
    assert reloaded.token_mapping == view.token_mapping
    assert reloaded.variant_mapping == view.variant_mapping
    assert reloaded.graphs == view.graphs
    assert reloaded.review_plan == view.review_plan
    assert reloaded.execution_order == view.execution_order
    assert reloaded.source_refs == view.source_refs
    assert reloaded.quality.overall_score == view.quality.overall_score


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = DesignExecutionPlanLineageId.new()
    await sql_env.facade.orchestrate(BuildExecutionPlan(request=request_factory(), lineage_id=lineage))
    await sql_env.facade.orchestrate(BuildExecutionPlan(request=request_factory(), lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [p.version for p in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
