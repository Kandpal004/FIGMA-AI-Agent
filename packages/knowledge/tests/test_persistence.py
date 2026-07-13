"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves the Postgres-shaped adapters durably persist entries and preserve full
version history, and that reasoning works identically over the database.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry, ReviseEntry
from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.shared.value_objects import Confidence, Platform, Priority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.inmemory import Clock
from knowledge.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)

NNG = Source(name="NNG", kind=SourceKind.RESEARCH_INSTITUTE)


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
async def sql_facade():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    env = build_sqlalchemy_environment(session_factory, clock=FixedClock())
    yield env.facade
    await engine.dispose()


async def _activate(facade, **kw):
    view = await facade.add(AddEntry(**kw))
    vid = EntryVersionId.from_string(view.entry_version_id)
    await facade.propose(ProposeEntry(entry_version_id=vid))
    return await facade.activate(ActivateEntry(entry_version_id=vid))


async def test_entry_is_durable_and_reasoning_works_over_db(sql_facade) -> None:
    facade = sql_facade
    hicks = await _activate(
        facade, category=KnowledgeCategory.UX_LAWS, title="Hick's Law",
        statement="Reduce choices to speed decisions.", description="d", source=NNG,
        confidence=Confidence.of(0.92), priority=Priority.HIGH,
        applicability=Applicability.build(page_types=["product"], platforms=[Platform.SHOPIFY_PLUS]),
    )
    # reload the exact version from the DB
    reloaded = await facade.get(EntryVersionId.from_string(hicks.entry_version_id))
    assert reloaded.title == "Hick's Law" and reloaded.status == "active"
    assert reloaded.page_types == ["product"] and reloaded.platforms == ["shopify_plus"]

    # reasoning over the database
    rationale = await facade.ask(DecisionContext.build(
        page_type="product", platform=Platform.SHOPIFY_PLUS,
        categories=[KnowledgeCategory.UX_LAWS]))
    assert rationale.primary is not None and rationale.primary.title == "Hick's Law"


async def test_versioning_history_is_retained_in_db(sql_facade) -> None:
    facade = sql_facade
    v1 = await _activate(
        facade, category=KnowledgeCategory.SPACING, title="8pt Grid",
        statement="Use an 8-point spacing grid.", description="d", source=NNG,
    )
    kid = KnowledgeId.from_string(v1.knowledge_id)
    v2 = await facade.revise(ReviseEntry(
        from_entry_version_id=EntryVersionId.from_string(v1.entry_version_id),
        statement="Use a 4/8-point spacing scale."))
    vid = EntryVersionId.from_string(v2.entry_version_id)
    await facade.propose(ProposeEntry(entry_version_id=vid))
    await facade.activate(ActivateEntry(entry_version_id=vid))

    current = await facade.get_active(kid)
    assert current.version == 2
    history = await facade.history(kid)
    assert [e.version for e in history] == [1, 2]
    assert history[0].status == "superseded"  # v1 superseded, retained
