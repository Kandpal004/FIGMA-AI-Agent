"""In-memory persistence for the Component Intelligence Engine.

A system clock and a dict-backed specification store + unit of work, so the engine runs and is
tested with no external services. Semantics match the real SQLAlchemy adapters.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from component_intelligence.application.ports.clock import Clock
from component_intelligence.domain.report.report import ComponentCompositionSpecification
from component_intelligence.domain.shared.ids import (
    ComponentSpecId,
    ComponentSpecLineageId,
)

__all__ = [
    "InMemorySpecificationRepository",
    "InMemoryUnitOfWork",
    "SpecificationStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class SpecificationStorage:
    """Process-lifetime storage for produced specifications."""

    def __init__(self) -> None:
        self.by_id: dict[ComponentSpecId, ComponentCompositionSpecification] = {}
        self.by_lineage: dict[
            ComponentSpecLineageId, list[ComponentCompositionSpecification]
        ] = {}


class InMemorySpecificationRepository:
    """Dict-backed :class:`ComponentSpecificationRepository`."""

    def __init__(self, storage: SpecificationStorage) -> None:
        self._storage = storage

    async def save(self, specification: ComponentCompositionSpecification) -> None:
        self._storage.by_id[specification.id] = specification
        versions = self._storage.by_lineage.setdefault(specification.lineage_id, [])
        versions[:] = [s for s in versions if s.id != specification.id]
        versions.append(specification)

    async def get(
        self, specification_id: ComponentSpecId
    ) -> ComponentCompositionSpecification:
        specification = self._storage.by_id.get(specification_id)
        if specification is None:
            raise NotFoundError(
                f"Specification {specification_id} not found.",
                details={"specification_id": str(specification_id)},
            )
        return specification

    async def latest(
        self, lineage_id: ComponentSpecLineageId
    ) -> ComponentCompositionSpecification:
        versions = self._storage.by_lineage.get(lineage_id)
        if not versions:
            raise NotFoundError(
                f"No specifications for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return max(versions, key=lambda s: s.version)

    async def history(
        self, lineage_id: ComponentSpecLineageId
    ) -> Sequence[ComponentCompositionSpecification]:
        versions = self._storage.by_lineage.get(lineage_id, [])
        return sorted(versions, key=lambda s: s.version)


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage."""

    def __init__(self, storage: SpecificationStorage) -> None:
        self.specifications = InMemorySpecificationRepository(storage)

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


def make_unit_of_work_factory(storage: SpecificationStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
