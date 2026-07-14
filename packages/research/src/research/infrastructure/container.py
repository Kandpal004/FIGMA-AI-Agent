"""Composition root — where concrete adapters meet the research application.

Assembles the engine (with its pipeline stages and registry) and the facade from
injected ports. Provides a batteries-included in-memory environment — a registry
pre-wired with the structured and HTML extractors and an in-memory source — and
helpers to build the engine over any registry, unit of work, and ports (e.g. the real
Knowledge/Memory adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from research.application.ports.clock import Clock
from research.application.ports.knowledge_link import KnowledgeLinkPort
from research.application.ports.unit_of_work import UnitOfWorkFactory
from research.application.research_engine import ResearchEngine
from research.application.source_registry import SourceRegistry
from research.domain.shared.value_objects import ArtifactKind, ProviderKind
from research.infrastructure.adapters.html_extractor import HtmlExtractor
from research.infrastructure.adapters.inmemory_source import InMemorySource
from research.infrastructure.adapters.structured_extractor import StructuredExtractor
from research.infrastructure.inmemory import (
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from research.interfaces.research_facade import ResearchFacade

__all__ = [
    "ResearchEnvironment",
    "build_default_registry",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_default_registry(
    *, in_memory_source: InMemorySource | None = None
) -> SourceRegistry:
    """A registry pre-wired with the structured + HTML extractors and an in-memory
    source registered for the manual/in-memory providers."""
    registry = SourceRegistry()
    source = in_memory_source or InMemorySource()
    registry.register_source(ProviderKind.IN_MEMORY, source)
    registry.register_source(ProviderKind.MANUAL, source)

    structured = StructuredExtractor()
    registry.register_extractor(
        structured,
        kinds=(ArtifactKind.STRUCTURED, ArtifactKind.JSON),
        default=True,
    )
    registry.register_extractor(HtmlExtractor(), kinds=(ArtifactKind.HTML,))
    return registry


def build_engine(
    *,
    registry: SourceRegistry,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
    knowledge_link: KnowledgeLinkPort | None = None,
) -> ResearchEngine:
    """Assemble a :class:`ResearchEngine` from its registry and ports."""
    return ResearchEngine(
        registry=registry,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
        knowledge_link=knowledge_link,
    )


def build_facade(
    engine: ResearchEngine, uow_factory: UnitOfWorkFactory
) -> ResearchFacade:
    """Wrap an engine in its inbound facade."""
    return ResearchFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class ResearchEnvironment:
    """A fully wired engine plus handles to its registry and in-memory report store."""

    facade: ResearchFacade
    engine: ResearchEngine
    registry: SourceRegistry
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    registry: SourceRegistry | None = None,
    knowledge_link: KnowledgeLinkPort | None = None,
    clock: Clock | None = None,
) -> ResearchEnvironment:
    """Stand up the whole engine over in-memory persistence."""
    registry = registry or build_default_registry()
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        registry=registry,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
        knowledge_link=knowledge_link,
    )
    facade = build_facade(engine, uow_factory)
    return ResearchEnvironment(
        facade=facade,
        engine=engine,
        registry=registry,
        storage=storage,
        unit_of_work_factory=uow_factory,
    )
