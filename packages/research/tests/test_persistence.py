"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves a produced report is stored as its codec document and reconstructed
(re-validated) on load, identical in content, and that versioning works in the DB.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from research.application.commands import Research
from research.domain.shared.ids import ResearchReportId, ResearchReportLineageId
from research.domain.shared.value_objects import ArtifactKind
from research.infrastructure.adapters.inmemory_source import InMemorySource
from research.infrastructure.container import build_default_registry
from research.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

from .conftest import STRUCTURED_PAYLOAD, FixedClock, make_artifact, make_source


@pytest.fixture
async def sql_env_factory():
    engines = []

    async def _make(artifacts_by_source):
        source = InMemorySource()
        for sid, arts in artifacts_by_source.items():
            source.register(sid, arts)
        registry = build_default_registry(in_memory_source=source)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        engines.append(engine)
        sf = async_sessionmaker(engine, expire_on_commit=False)
        await init_models(engine)
        return build_sqlalchemy_environment(sf, registry=registry, clock=FixedClock())

    yield _make
    for engine in engines:
        await engine.dispose()


async def test_report_round_trips_through_the_database(sql_env_factory, request_factory):
    source = make_source(uri="https://acme.example")
    artifact = make_artifact(source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD)
    env = await sql_env_factory({source.id: [artifact]})

    view = await env.facade.research(Research(request=request_factory(source)))
    rid = ResearchReportId.from_string(view.report_id)

    reloaded = await env.facade.get(rid)  # decoded + re-validated from the DB
    assert reloaded.report_id == view.report_id
    assert reloaded.version == view.version
    assert reloaded.quality.quality_score == view.quality.quality_score
    assert len(reloaded.evidence) == len(view.evidence) == 2
    assert len(reloaded.entities) == len(view.entities) == 2
    assert len(reloaded.relationships) == len(view.relationships) == 1
    assert {e.claim for e in reloaded.evidence} == {e.claim for e in view.evidence}


async def test_versioning_persists_across_the_database(sql_env_factory, request_factory):
    source = make_source(uri="https://acme.example")
    artifact = make_artifact(source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD)
    env = await sql_env_factory({source.id: [artifact]})

    lineage = ResearchReportLineageId.new()
    req = request_factory(source)
    await env.facade.research(Research(request=req, lineage_id=lineage))
    await env.facade.research(Research(request=req, lineage_id=lineage))

    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    latest = await env.facade.latest(lineage)
    assert latest.version == 2
