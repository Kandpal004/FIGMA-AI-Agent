"""The ApprovalBundle — the neutral go/no-go hand-off downstream phases consume.

The Creative Director is the gate every phase obeys. Rather than expose its full internal
review, it emits this compact, self-contained bundle — the ruling, whether the run may
proceed, the overall score, and the ranked required changes a rejected phase must address.
The orchestration layer (and a future Figma phase) reads this to decide whether to advance or
loop back, without importing the review's internals.

Pure domain: standard library and the review models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from creative_director.domain.finding.finding import RequiredChange
from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.shared.ids import CreativeDirectorReviewId
from creative_director.domain.shared.value_objects import ApprovalStatus, Score

__all__ = ["ApprovalBundle"]


@dataclass(frozen=True, slots=True)
class ApprovalBundle:
    """The neutral ruling a downstream phase acts on.

    Attributes:
        review_id: The review version this bundle projects.
        project_id: The owning project.
        subject_reference: The artifact that was reviewed.
        status: The Creative Director's ruling.
        can_proceed: Whether the run may advance.
        overall_score: The overall quality score of the subject.
        required_changes: The ranked changes a rejected subject must address.
        created_at: When the review was produced.
    """

    review_id: CreativeDirectorReviewId
    project_id: str
    subject_reference: str
    status: ApprovalStatus
    can_proceed: bool
    overall_score: Score
    required_changes: tuple[RequiredChange, ...]
    created_at: datetime

    @classmethod
    def from_review(cls, review: CreativeDirectorReview) -> ApprovalBundle:
        return cls(
            review_id=review.id,
            project_id=review.project_id,
            subject_reference=review.subject.reference,
            status=review.approval.status,
            can_proceed=review.can_proceed,
            overall_score=review.scorecard.overall,
            required_changes=tuple(review.improvement_matrix),
            created_at=review.created_at,
        )
