"""Shared fixtures for the Knowledge Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.infrastructure.container import (
    KnowledgeEnvironment,
    build_in_memory_environment,
)
from knowledge.infrastructure.inmemory import Clock


class FixedClock(Clock):
    """Deterministic clock for repeatable timestamps."""

    def now(self) -> datetime:
        return datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def env() -> KnowledgeEnvironment:
    """A fully-wired in-memory Knowledge Engine."""
    return build_in_memory_environment(clock=FixedClock())


@pytest.fixture
def author_active(env: KnowledgeEnvironment):
    """Helper: author -> propose -> activate, returning the ACTIVE EntryView."""

    async def _author(**kwargs) -> object:
        view = await env.facade.add(AddEntry(**kwargs))
        from knowledge.domain.shared.ids import EntryVersionId

        vid = EntryVersionId.from_string(view.entry_version_id)
        await env.facade.propose(ProposeEntry(entry_version_id=vid))
        return await env.facade.activate(ActivateEntry(entry_version_id=vid))

    return _author
