"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced report is stored as its codec document and reconstructed
(re-validated) on load, identical in content, and that versioning works in the DB.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from psychology.application.commands import BuildPsychology
from psychology.domain.shared.ids import PsychologyReportId, PsychologyReportLineageId
from psychology.domain.shared.value_objects import ProvenanceKind
from psychology.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryKnowledgeAdvisor,
)
from psychology.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import FixedClock, signal


def _signals():
    return [
        signal(ProvenanceKind.BRAND_STRATEGY, "b1", "Evoke trust and confidence", 0.9, "trust", "emotion"),
        signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Premium value; reviews and guarantees required", 0.9, "premium", "trust", "review"),
        signal(ProvenanceKind.KNOWLEDGE, "k1", "Social proof reduces anxiety", 0.85, "social", "proof"),
    ]


@pytest.fixture
async def sql_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    ins = _signals()
    env = build_sqlalchemy_environment(
        sf,
        brand=InMemoryBrandInput([i for i in ins if i.provenance is ProvenanceKind.BRAND_STRATEGY]),
        business_strategy=InMemoryBusinessStrategyInput([i for i in ins if i.provenance is ProvenanceKind.BUSINESS_STRATEGY]),
        knowledge=InMemoryKnowledgeAdvisor([i for i in ins if i.provenance is ProvenanceKind.KNOWLEDGE]),
        clock=FixedClock(),
    )
    yield env
    await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env, request_factory):
    view = await sql_env.facade.build(BuildPsychology(request=request_factory()))
    rid = PsychologyReportId.from_string(view.report_id)

    reloaded = await sql_env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.version == view.version
    assert reloaded.awareness == view.awareness
    assert reloaded.sophistication == view.sophistication
    assert reloaded.quality.overall_score == view.quality.overall_score
    assert reloaded.evidence_count == view.evidence_count
    assert reloaded.matrices == view.matrices  # the full nine-matrix document round-trips
    assert reloaded.graphs == view.graphs  # the six graphs round-trip
    assert reloaded.frameworks == view.frameworks


async def test_versioning_persists_across_the_database(sql_env, request_factory):
    lineage = PsychologyReportLineageId.new()
    req = request_factory()
    await sql_env.facade.build(BuildPsychology(request=req, lineage_id=lineage))
    await sql_env.facade.build(BuildPsychology(request=req, lineage_id=lineage))

    history = await sql_env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await sql_env.facade.latest(lineage)).version == 2
