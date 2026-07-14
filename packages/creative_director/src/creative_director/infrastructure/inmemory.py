"""In-memory persistence for the Creative Director Engine.

A system clock and a dict-backed review store + unit of work, so the engine runs and is tested
with no external services. Semantics match the real SQLAlchemy adapters.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from creative_director.application.ports.clock import Clock
from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.shared.ids import (
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)

__all__ = [
    "InMemoryReviewRepository",
    "InMemoryUnitOfWork",
    "ReviewStorage",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ReviewStorage:
    """Process-lifetime storage for produced reviews."""

    def __init__(self) -> None:
        self.by_id: dict[CreativeDirectorReviewId, CreativeDirectorReview] = {}
        self.by_lineage: dict[
            CreativeDirectorReviewLineageId, list[CreativeDirectorReview]
        ] = {}


class InMemoryReviewRepository:
    """Dict-backed :class:`CreativeDirectorReviewRepository`."""

    def __init__(self, storage: ReviewStorage) -> None:
        self._storage = storage

    async def save(self, review: CreativeDirectorReview) -> None:
        self._storage.by_id[review.id] = review
        versions = self._storage.by_lineage.setdefault(review.lineage_id, [])
        versions[:] = [r for r in versions if r.id != review.id]
        versions.append(review)

    async def get(self, review_id: CreativeDirectorReviewId) -> CreativeDirectorReview:
        review = self._storage.by_id.get(review_id)
        if review is None:
            raise NotFoundError(
                f"Review {review_id} not found.", details={"review_id": str(review_id)}
            )
        return review

    async def latest(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> CreativeDirectorReview:
        versions = self._storage.by_lineage.get(lineage_id)
        if not versions:
            raise NotFoundError(
                f"No reviews for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return max(versions, key=lambda r: r.version)

    async def history(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> Sequence[CreativeDirectorReview]:
        versions = self._storage.by_lineage.get(lineage_id, [])
        return sorted(versions, key=lambda r: r.version)


class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage."""

    def __init__(self, storage: ReviewStorage) -> None:
        self.reviews = InMemoryReviewRepository(storage)

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


def make_unit_of_work_factory(storage: ReviewStorage):
    """Return a zero-arg factory opening units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory
