"""SQLAlchemy implementation of the review repository.

Persists a review as its codec document plus indexed columns, and reconstructs it
(re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.shared.ids import (
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)
from creative_director.infrastructure.persistence import codec
from creative_director.infrastructure.persistence.models import CreativeDirectorReviewModel

__all__ = ["SqlAlchemyReviewRepository"]


class SqlAlchemyReviewRepository:
    """Database-backed :class:`CreativeDirectorReviewRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, review: CreativeDirectorReview) -> None:
        document = codec.to_document(review)
        model = await self._session.get(CreativeDirectorReviewModel, review.id.value)
        if model is None:
            self._session.add(
                CreativeDirectorReviewModel(
                    id=review.id.value,
                    lineage_id=review.lineage_id.value,
                    version=review.version,
                    project_id=review.project_id,
                    subject_reference=review.subject.reference,
                    profile=review.policy.profile.kind.value,
                    mode=review.policy.mode.value,
                    approval_status=review.approval.status.value,
                    overall_score=review.scorecard.overall.value,
                    document=document,
                    created_at=review.created_at,
                )
            )
        else:
            model.version = review.version
            model.approval_status = review.approval.status.value
            model.overall_score = review.scorecard.overall.value
            model.document = document

    async def get(self, review_id: CreativeDirectorReviewId) -> CreativeDirectorReview:
        model = await self._session.get(CreativeDirectorReviewModel, review_id.value)
        if model is None:
            raise NotFoundError(
                f"Review {review_id} not found.", details={"review_id": str(review_id)}
            )
        return codec.from_document(model.document)

    async def latest(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> CreativeDirectorReview:
        stmt = (
            select(CreativeDirectorReviewModel)
            .where(CreativeDirectorReviewModel.lineage_id == lineage_id.value)
            .order_by(CreativeDirectorReviewModel.version.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalars().first()
        if model is None:
            raise NotFoundError(
                f"No reviews for lineage {lineage_id}.",
                details={"lineage_id": str(lineage_id)},
            )
        return codec.from_document(model.document)

    async def history(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> Sequence[CreativeDirectorReview]:
        stmt = (
            select(CreativeDirectorReviewModel)
            .where(CreativeDirectorReviewModel.lineage_id == lineage_id.value)
            .order_by(CreativeDirectorReviewModel.version.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [codec.from_document(m.document) for m in rows]
