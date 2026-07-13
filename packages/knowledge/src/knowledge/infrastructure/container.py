"""Composition roots — where concrete adapters meet the application.

The single seam that wires the reasoner, query service, and authoring service —
and the facade over them — from injected ports. Provides a batteries-included
in-memory environment (runnable with zero external services) and a database-backed
environment over a SQLAlchemy session factory. Nothing in ``domain`` or
``application`` imports this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.application.authoring_service import KnowledgeAuthoringService
from knowledge.application.ports.clock import Clock
from knowledge.application.ports.repository import KnowledgeRepository
from knowledge.application.ports.search_port import KnowledgeSearchPort
from knowledge.application.ports.unit_of_work import UnitOfWorkFactory
from knowledge.application.query_service import KnowledgeQueryService
from knowledge.application.reasoner import KnowledgeReasoner
from knowledge.infrastructure.inmemory import (
    InMemoryKnowledgeRepository,
    InMemoryKnowledgeSearchPort,
    InMemoryStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from knowledge.interfaces.knowledge_facade import KnowledgeFacade

__all__ = [
    "KnowledgeEnvironment",
    "build_facade",
    "build_in_memory_environment",
]


def build_facade(
    *,
    repository: KnowledgeRepository,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
    search: KnowledgeSearchPort | None = None,
) -> KnowledgeFacade:
    """Assemble the facade (and the services it fronts) from ports."""
    query_service = KnowledgeQueryService(repository, search)
    reasoner = KnowledgeReasoner(repository)
    authoring = KnowledgeAuthoringService(
        unit_of_work_factory=unit_of_work_factory, clock=clock
    )
    return KnowledgeFacade(
        reasoner=reasoner, query_service=query_service, authoring_service=authoring
    )


@dataclass(frozen=True, slots=True)
class KnowledgeEnvironment:
    """A fully wired engine plus a handle to its in-memory backing store."""

    facade: KnowledgeFacade
    storage: InMemoryStorage
    repository: KnowledgeRepository
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *, clock: Clock | None = None, with_search: bool = True
) -> KnowledgeEnvironment:
    """Stand up the whole engine backed entirely by in-memory adapters."""
    storage = InMemoryStorage()
    repository = InMemoryKnowledgeRepository(storage)
    uow_factory = make_unit_of_work_factory(storage)
    search = InMemoryKnowledgeSearchPort(storage) if with_search else None
    facade = build_facade(
        repository=repository,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
        search=search,
    )
    return KnowledgeEnvironment(
        facade=facade,
        storage=storage,
        repository=repository,
        unit_of_work_factory=uow_factory,
    )
