"""The Review repository port — persistence for produced reviews.

Reviews are versioned; the repository stores each version and can return the latest by lineage
and the full history. The infrastructure layer supplies concrete implementations; tests
supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.shared.ids import (
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)

__all__ = ["CreativeDirectorReviewRepository"]


@runtime_checkable
class CreativeDirectorReviewRepository(Protocol):
    """Persists and loads :class:`CreativeDirectorReview` versions."""

    async def save(self, review: CreativeDirectorReview) -> None:
        """Persist a review version (insert or update by id)."""
        ...

    async def get(self, review_id: CreativeDirectorReviewId) -> CreativeDirectorReview:
        """Return a review by id.

        Raises:
            NotFoundError: If no such review exists.
        """
        ...

    async def latest(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> CreativeDirectorReview:
        """Return the highest-version review of a lineage.

        Raises:
            NotFoundError: If the lineage has no reviews.
        """
        ...

    async def history(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> Sequence[CreativeDirectorReview]:
        """Return every version of a lineage, oldest first."""
        ...
