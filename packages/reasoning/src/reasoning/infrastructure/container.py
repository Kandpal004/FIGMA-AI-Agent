"""Composition root — where concrete adapters meet the reasoning application.

Assembles the nine dimension reasoners, the engine, and the facade from injected
ports. Provides a batteries-included in-memory environment (runnable with a
scriptable advisor, no external services) and a helper to build the engine over
any set of ports (e.g. the real Knowledge/Memory adapters).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from reasoning.application.dimensions.base import DimensionReasoner
from reasoning.application.dimensions.business import BusinessReasoner
from reasoning.application.dimensions.competitive import CompetitiveReasoner
from reasoning.application.dimensions.conversion import ConversionReasoner
from reasoning.application.dimensions.customer import CustomerReasoner
from reasoning.application.dimensions.experience import ExperienceReasoner
from reasoning.application.dimensions.platform import PlatformReasoner
from reasoning.application.dimensions.review import ReviewReasoner
from reasoning.application.dimensions.structure import StructureReasoner
from reasoning.application.dimensions.visual import VisualReasoner
from reasoning.application.ports.clock import Clock
from reasoning.application.ports.context_port import ContextPort
from reasoning.application.ports.decision_history_port import DecisionHistoryPort
from reasoning.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from reasoning.application.ports.unit_of_work import UnitOfWorkFactory
from reasoning.application.reasoning_engine import ReasoningEngine
from reasoning.infrastructure.inmemory import (
    InMemoryKnowledgeAdvisor,
    NullContextPort,
    NullDecisionHistoryPort,
    StrategyStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from reasoning.interfaces.reasoning_facade import ReasoningFacade

__all__ = [
    "DEFAULT_REASONERS",
    "ReasoningEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
    "default_reasoners",
]


def default_reasoners() -> tuple[DimensionReasoner, ...]:
    """The canonical nine dimension reasoners, in execution order."""
    return (
        BusinessReasoner(),
        CustomerReasoner(),
        ConversionReasoner(),
        ExperienceReasoner(),
        PlatformReasoner(),
        CompetitiveReasoner(),
        VisualReasoner(),
        StructureReasoner(),
        ReviewReasoner(),
    )


#: The default reasoner set (evaluated once).
DEFAULT_REASONERS: tuple[DimensionReasoner, ...] = default_reasoners()


def build_engine(
    *,
    advisor: KnowledgeAdvisorPort,
    context_port: ContextPort,
    decision_history_port: DecisionHistoryPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
    reasoners: Sequence[DimensionReasoner] | None = None,
) -> ReasoningEngine:
    """Assemble a :class:`ReasoningEngine` from its ports."""
    return ReasoningEngine(
        reasoners=tuple(reasoners) if reasoners is not None else default_reasoners(),
        advisor=advisor,
        context_port=context_port,
        decision_history_port=decision_history_port,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(engine: ReasoningEngine, uow_factory: UnitOfWorkFactory) -> ReasoningFacade:
    """Wrap an engine in its inbound facade."""
    return ReasoningFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class ReasoningEnvironment:
    """A fully wired engine plus a handle to its in-memory strategy store."""

    facade: ReasoningFacade
    engine: ReasoningEngine
    storage: StrategyStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    advisor: KnowledgeAdvisorPort | None = None,
    *,
    context_port: ContextPort | None = None,
    decision_history_port: DecisionHistoryPort | None = None,
    clock: Clock | None = None,
) -> ReasoningEnvironment:
    """Stand up the whole engine over in-memory adapters.

    A scriptable :class:`InMemoryKnowledgeAdvisor` is used by default; pass the
    real :class:`KnowledgeAdvisorAdapter` to reason over the actual corpus.
    """
    storage = StrategyStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        advisor=advisor or InMemoryKnowledgeAdvisor(),
        context_port=context_port or NullContextPort(),
        decision_history_port=decision_history_port or NullDecisionHistoryPort(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return ReasoningEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
