"""Composition root — where concrete adapters meet the intelligence application.

Assembles the engine (with its analyzers) and the facade from injected ports.
Provides a batteries-included in-memory environment (runnable with a static data
source and a scriptable advisor) and a helper to build the engine over any ports
(e.g. the real Knowledge/Reasoning adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from competitive.application.intelligence_engine import IntelligenceEngine
from competitive.application.ports.clock import Clock
from competitive.application.ports.data_source import CompetitorDataSourcePort
from competitive.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from competitive.application.ports.reasoning import ReasoningPort
from competitive.application.ports.unit_of_work import UnitOfWorkFactory
from competitive.infrastructure.inmemory import (
    NullReasoningPort,
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from competitive.interfaces.intelligence_facade import IntelligenceFacade

__all__ = [
    "IntelligenceEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    data_source: CompetitorDataSourcePort,
    advisor: KnowledgeAdvisorPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
    reasoning: ReasoningPort | None = None,
) -> IntelligenceEngine:
    """Assemble an :class:`IntelligenceEngine` from its ports."""
    return IntelligenceEngine(
        data_source=data_source,
        advisor=advisor,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
        reasoning=reasoning,
    )


def build_facade(
    engine: IntelligenceEngine, uow_factory: UnitOfWorkFactory
) -> IntelligenceFacade:
    """Wrap an engine in its inbound facade."""
    return IntelligenceFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class IntelligenceEnvironment:
    """A fully wired engine plus a handle to its in-memory report store."""

    facade: IntelligenceFacade
    engine: IntelligenceEngine
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    data_source: CompetitorDataSourcePort,
    advisor: KnowledgeAdvisorPort,
    reasoning: ReasoningPort | None = None,
    clock: Clock | None = None,
) -> IntelligenceEnvironment:
    """Stand up the whole engine over in-memory persistence."""
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        data_source=data_source,
        advisor=advisor,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
        reasoning=reasoning or NullReasoningPort(),
    )
    facade = build_facade(engine, uow_factory)
    return IntelligenceEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
