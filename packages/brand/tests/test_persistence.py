"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced report is stored as its codec document and reconstructed
(re-validated) on load, identical in content, and that versioning works in the DB.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from brand.application.commands import BuildBrand
from brand.domain.shared.ids import BrandReportId, BrandReportLineageId
from brand.domain.shared.value_objects import ProvenanceKind
from brand.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput,
    InMemoryKnowledgeAdvisor,
)
from brand.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import FixedClock, signal


def _signals():
    return [
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Position as premium: trusted value", 0.9, "premium", "positioning"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s2", "Evoke trust and confidence", 0.85, "trust", "emotion"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Editorial serif conveys premium credibility", 0.8, "typography", "premium"),
    ]


@pytest.fixture
async def sql_env(request_factory):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    ins = _signals()
    env = build_sqlalchemy_environment(
        sf,
        business_strategy=InMemoryBusinessStrategyInput([i for i in ins if i.provenance is ProvenanceKind.BUSINESS_STRATEGY]),
        knowledge=InMemoryKnowledgeAdvisor([i for i in ins if i.provenance is ProvenanceKind.KNOWLEDGE]),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.build(BuildBrand(request=request_factory()))
    rid = BrandReportId.from_string(view.report_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.version == view.version
    assert reloaded.primary_category == view.primary_category
    assert reloaded.archetype == view.archetype
    assert reloaded.quality.overall_score == view.quality.overall_score
    assert len(reloaded.decisions) == len(view.decisions)
    assert reloaded.evidence_count == view.evidence_count
    assert len(reloaded.validation_rules) == len(view.validation_rules)
    assert reloaded.identity.positioning == view.identity.positioning
    assert reloaded.visual.direction == view.visual.direction


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = BrandReportLineageId.new()
    req = request_factory()
    await sql_env.facade.build(BuildBrand(request=req, lineage_id=lineage))
    await sql_env.facade.build(BuildBrand(request=req, lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
