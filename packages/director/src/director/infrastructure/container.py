"""Composition root — the one place concrete adapters meet the application.

Clean Architecture forbids the application and domain from knowing which concrete
adapters they run against. This module is the single seam where that wiring
happens: it constructs a :class:`DirectorService` (and a :class:`DirectorFacade`)
from injected ports, and offers a batteries-included in-memory environment so the
whole engine can be stood up in one call for local running and tests.

Nothing in ``domain`` or ``application`` imports this module; only an entry point
(the API app, a worker, or a test) does.
"""

from __future__ import annotations

from dataclasses import dataclass

from director.application.director.director_service import (
    DEFAULT_MAX_REDESIGNS,
    DirectorService,
)
from director.application.memory.memory_engine import MemoryEngine
from director.application.ports.agent_executor_port import AgentExecutorPort
from director.application.ports.clock import Clock
from director.application.ports.memory_port import MemoryStore
from director.application.ports.unit_of_work import UnitOfWorkFactory
from director.application.state.state_engine import StateEngine
from director.application.workflow.workflow_engine import WorkflowEngine
from director.domain.state.transitions import StepStateMachine
from director.domain.workflow.catalog import WorkflowCatalog
from director.infrastructure.inmemory import (
    InMemoryMemoryStore,
    InMemoryStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from director.interfaces.director_facade import DirectorFacade

__all__ = ["DirectorEnvironment", "build_director", "build_in_memory_environment"]


def build_director(
    *,
    catalog: WorkflowCatalog,
    agent_executor: AgentExecutorPort,
    unit_of_work_factory: UnitOfWorkFactory,
    memory_store: MemoryStore,
    clock: Clock,
    max_redesigns: int = DEFAULT_MAX_REDESIGNS,
) -> DirectorService:
    """Assemble a :class:`DirectorService` from its ports.

    This is the canonical wiring: the three application engines are built here
    over the injected catalog, state machine, and memory store, and handed to the
    Director along with the executor, unit-of-work factory, and clock.
    """
    return DirectorService(
        workflow_engine=WorkflowEngine(catalog),
        state_engine=StateEngine(StepStateMachine()),
        memory_engine=MemoryEngine(memory_store),
        agent_executor=agent_executor,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
        max_redesigns=max_redesigns,
    )


@dataclass(frozen=True, slots=True)
class DirectorEnvironment:
    """A fully wired engine plus handles to its in-memory backing stores.

    The stores are exposed so tests and local tools can seed projects and inspect
    persisted state without going through the ports.
    """

    facade: DirectorFacade
    director: DirectorService
    storage: InMemoryStorage
    memory_store: InMemoryMemoryStore
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    agent_executor: AgentExecutorPort,
    *,
    catalog: WorkflowCatalog | None = None,
    clock: Clock | None = None,
    max_redesigns: int = DEFAULT_MAX_REDESIGNS,
) -> DirectorEnvironment:
    """Stand up the whole engine backed entirely by in-memory adapters.

    Only the agent executor must be supplied (it is what actually runs agents);
    everything else — storage, memory, clock, catalog — defaults to an in-memory
    or canonical implementation. Ideal for tests and local experimentation.
    """
    storage = InMemoryStorage()
    memory_store = InMemoryMemoryStore()
    uow_factory = make_unit_of_work_factory(storage)
    resolved_catalog = catalog or WorkflowCatalog.default()

    director = build_director(
        catalog=resolved_catalog,
        agent_executor=agent_executor,
        unit_of_work_factory=uow_factory,
        memory_store=memory_store,
        clock=clock or SystemClock(),
        max_redesigns=max_redesigns,
    )
    facade = DirectorFacade(director, uow_factory)
    return DirectorEnvironment(
        facade=facade,
        director=director,
        storage=storage,
        memory_store=memory_store,
        unit_of_work_factory=uow_factory,
    )
