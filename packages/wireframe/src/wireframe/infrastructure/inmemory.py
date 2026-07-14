"""In-memory persistence for the Wireframe Planning Engine.

A system clock and a dict-backed plan store + unit of work, so the engine runs and is tested
with no external services. Semantics match the real SQLAlchemy adapters.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from wireframe.application.ports.clock import Clock
from wireframe.domain.report.report import WireframePlan
from wireframe.domain.shared.ids import WireframePlanId, WireframePlanLineageId

__all__ = [
    "InMemoryWireframePlanRepository",
    "InMemoryUnitOfWork",
    "PlanStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class PlanStorage:
    """Process-lifetime storage for produced plans."""

    def __init__(self) -> None:
        self.by_id: dict[WireframePlanId, WireframePlan] = {}
        self.by_lineage: dict[WireframePlanLineageId, list[WireframePlan]] = {}


class InMemoryWireframePlanRepository:
    """Dict-backed :class:`WireframePlanRepository`."""

    def __init__(self, storage: PlanStorage) -> None:
        self._storage = storage

    async def save(self, plan: WireframePlan) -> None:
        self._storage.by_id[plan.id] = plan
        versions = self._storage.by_lineage.setdefault(plan.lineage_id, [])
        versions[:] = [p for p in versions if p.id != plan.id]
        versions.append(plan)

    async def get(self, plan_id: WireframePlanId) -> WireframePlan:
        plan = self._storage.by_id.get(plan_id)
        if plan is None:
            raise NotFoundError(
                f"Plan {plan_id} not found.", details={"plan_id": str(plan_id)}
            )
        return plan

    async def latest(self, lineage_id: WireframePlanLineageId) -> WireframePlan:
        versions = self._storage.by_lineage.get(lineage_id)
        if not versions:
            raise NotFoundError(
                f"No plans for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return max(versions, key=lambda p: p.version)

    async def history(self, lineage_id: WireframePlanLineageId) -> Sequence[WireframePlan]:
        versions = self._storage.by_lineage.get(lineage_id, [])
        return sorted(versions, key=lambda p: p.version)


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage."""

    def __init__(self, storage: PlanStorage) -> None:
        self.plans = InMemoryWireframePlanRepository(storage)

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


def make_unit_of_work_factory(storage: PlanStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
