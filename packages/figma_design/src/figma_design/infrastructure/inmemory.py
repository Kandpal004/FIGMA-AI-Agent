"""In-memory persistence for the Figma Design Engine.

A system clock and a dict-backed model store + unit of work, so the engine runs and is tested with
no external services. Semantics match the real SQLAlchemy adapters.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from figma_design.application.ports.clock import Clock
from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.shared.ids import (
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
)

__all__ = [
    "InMemoryModelRepository",
    "InMemoryUnitOfWork",
    "ModelStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ModelStorage:
    """Process-lifetime storage for produced models."""

    def __init__(self) -> None:
        self.by_id: dict[FigmaDesignModelId, FigmaDesignModel] = {}
        self.by_lineage: dict[FigmaDesignModelLineageId, list[FigmaDesignModel]] = {}


class InMemoryModelRepository:
    """Dict-backed :class:`FigmaModelRepository`."""

    def __init__(self, storage: ModelStorage) -> None:
        self._storage = storage

    async def save(self, model: FigmaDesignModel) -> None:
        self._storage.by_id[model.id] = model
        versions = self._storage.by_lineage.setdefault(model.lineage_id, [])
        versions[:] = [m for m in versions if m.id != model.id]
        versions.append(model)

    async def get(self, model_id: FigmaDesignModelId) -> FigmaDesignModel:
        model = self._storage.by_id.get(model_id)
        if model is None:
            raise NotFoundError(
                f"Model {model_id} not found.", details={"model_id": str(model_id)}
            )
        return model

    async def latest(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> FigmaDesignModel:
        versions = self._storage.by_lineage.get(lineage_id)
        if not versions:
            raise NotFoundError(
                f"No models for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return max(versions, key=lambda m: m.version)

    async def history(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> Sequence[FigmaDesignModel]:
        versions = self._storage.by_lineage.get(lineage_id, [])
        return sorted(versions, key=lambda m: m.version)


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage."""

    def __init__(self, storage: ModelStorage) -> None:
        self.models = InMemoryModelRepository(storage)

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


def make_unit_of_work_factory(storage: ModelStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
