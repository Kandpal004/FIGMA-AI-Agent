"""In-memory infrastructure for the Reasoning Engine.

Real, dependency-free implementations of every port, so the engine runs and is
tested with no external services. It includes a scriptable in-memory knowledge
advisor (for standalone use without Phase 3), an in-memory strategy store and unit
of work, null context/history ports (the honest "no external context" defaults),
and a system clock. All semantics match the real adapters.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from reasoning.application.ports.clock import Clock
from reasoning.application.ports.knowledge_advisor import AdvisedPrinciple
from reasoning.domain.request.request import BrandContext, ContextFact, PriorDecisionRef
from reasoning.domain.shared.ids import StrategyId
from reasoning.domain.shared.value_objects import ReasoningDimension
from reasoning.domain.strategy.strategy import DesignStrategy

__all__ = [
    "InMemoryKnowledgeAdvisor",
    "InMemoryStrategyRepository",
    "InMemoryUnitOfWork",
    "NullContextPort",
    "NullDecisionHistoryPort",
    "StrategyStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class InMemoryKnowledgeAdvisor:
    """A scriptable advisor returning fixed principles per dimension.

    Useful for standalone runs and tests without wiring the full Knowledge
    Engine; the real :class:`KnowledgeAdvisorAdapter` is swapped in for production.
    """

    def __init__(
        self, principles: Mapping[ReasoningDimension, Sequence[AdvisedPrinciple]] | None = None
    ) -> None:
        self._principles: dict[ReasoningDimension, tuple[AdvisedPrinciple, ...]] = {
            dimension: tuple(items) for dimension, items in (principles or {}).items()
        }

    async def advise(
        self,
        dimension: ReasoningDimension,
        *,
        page_type: str | None = None,
        component_type: str | None = None,
        platform: str | None = None,
        contexts: Sequence[str] = (),
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[AdvisedPrinciple]:
        items = self._principles.get(dimension, ())
        return items[:limit] if limit is not None else items


class NullContextPort:
    """A context port that supplies no brand or memory facts."""

    async def load_brand(
        self, project_id: str, *, tenant_id: object | None = None
    ) -> BrandContext:
        return BrandContext()

    async def load_memory_facts(
        self,
        project_id: str,
        *,
        section_id: str | None = None,
        tenant_id: object | None = None,
    ) -> Sequence[ContextFact]:
        return ()


class NullDecisionHistoryPort:
    """A decision-history port that supplies no prior decisions."""

    async def load_prior_decisions(
        self,
        project_id: str,
        *,
        section_id: str | None = None,
        tenant_id: object | None = None,
    ) -> Sequence[PriorDecisionRef]:
        return ()


class StrategyStorage:
    """Process-lifetime storage for produced strategies."""

    def __init__(self) -> None:
        self.strategies: dict[StrategyId, DesignStrategy] = {}


class InMemoryStrategyRepository:
    """Dict-backed :class:`StrategyRepository`."""

    def __init__(self, storage: StrategyStorage) -> None:
        self._storage = storage

    async def save(self, strategy: DesignStrategy) -> None:
        self._storage.strategies[strategy.id] = strategy

    async def get(self, strategy_id: StrategyId) -> DesignStrategy:
        strategy = self._storage.strategies.get(strategy_id)
        if strategy is None:
            raise NotFoundError(
                f"Strategy {strategy_id} not found.",
                details={"strategy_id": str(strategy_id)},
            )
        return strategy


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage."""

    def __init__(self, storage: StrategyStorage) -> None:
        self.strategies = InMemoryStrategyRepository(storage)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def make_unit_of_work_factory(storage: StrategyStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
