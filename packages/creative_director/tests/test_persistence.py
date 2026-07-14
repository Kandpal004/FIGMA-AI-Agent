"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced review is stored as its codec document and reconstructed (re-validated) on
load, identical in content — dimension verdicts, scores, approval, decision history, and all
five graphs — and that lineage versioning works in the database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from creative_director.application.commands import BuildReview
from creative_director.domain.shared.ids import (
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)
from creative_director.domain.shared.value_objects import ProvenanceKind
from creative_director.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from creative_director.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import FixedClock


@pytest.fixture
async def sql_env(strong_signals):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)

    def bucket(kind: ProvenanceKind):
        return [s for s in strong_signals if s.provenance is kind]

    P = ProvenanceKind
    env = build_sqlalchemy_environment(
        sf,
        wireframe=InMemoryWireframeInput(bucket(P.WIREFRAME)),
        ia=InMemoryIAInput(bucket(P.INFORMATION_ARCHITECTURE)),
        ux=InMemoryUXInput(bucket(P.UX_STRATEGY)),
        business_strategy=InMemoryBusinessStrategyInput(bucket(P.BUSINESS_STRATEGY)),
        brand=InMemoryBrandInput(bucket(P.BRAND_STRATEGY)),
        psychology=InMemoryPsychologyInput(bucket(P.PSYCHOLOGY)),
        knowledge=InMemoryKnowledgeAdvisor(bucket(P.KNOWLEDGE)),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_review_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.review(BuildReview(request=request_factory()))
    rid = CreativeDirectorReviewId.from_string(view.review_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.review_id == view.review_id
    assert reloaded.version == view.version
    assert reloaded.approval == view.approval
    assert reloaded.scorecard == view.scorecard
    assert reloaded.dimension_reviews == view.dimension_reviews
    assert reloaded.decision_history == view.decision_history
    assert reloaded.graphs == view.graphs
    assert reloaded.can_proceed == view.can_proceed


async def test_versioning_and_override_persist(sql_env, request_factory):
    from creative_director.application.commands import OverrideDecision
    from creative_director.domain.shared.value_objects import ApprovalStatus

    lineage = CreativeDirectorReviewLineageId.new()
    v1 = await sql_env.facade.review(BuildReview(request=request_factory(), lineage_id=lineage))
    await sql_env.facade.override(OverrideDecision(
        review_id=CreativeDirectorReviewId.from_string(v1.review_id),
        status=ApprovalStatus.REJECTED, rationale="Vetoed on review.",
    ))
    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).approval["decided_by"] == "creative_director"
