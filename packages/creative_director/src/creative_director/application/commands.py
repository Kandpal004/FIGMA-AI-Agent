"""Command objects — the engine's typed inputs.

* :class:`BuildReview` — run a fresh Creative Director review (a new version under a lineage).
* :class:`OverrideDecision` — a human Creative Director's ruling that supersedes the
  automatic one (also used to resolve a human-assisted escalation), producing a new version.
* :class:`CommitteeVote` — a set of committee verdicts aggregated into a new version.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.application.request import ReviewRequest
from creative_director.domain.shared.ids import (
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)
from creative_director.domain.shared.value_objects import ApprovalStatus

__all__ = ["BuildReview", "CommitteeBallot", "CommitteeVote", "OverrideDecision"]


@dataclass(frozen=True, slots=True)
class BuildReview:
    """Run a review for a request.

    Attributes:
        request: What to review and how strictly.
        lineage_id: The review lineage to append a new version to; ``None`` starts fresh.
    """

    request: ReviewRequest
    lineage_id: CreativeDirectorReviewLineageId | None = None


@dataclass(frozen=True, slots=True)
class OverrideDecision:
    """A human Creative Director's ruling that supersedes the automatic decision.

    Attributes:
        review_id: The review version being overridden.
        status: The human ruling.
        rationale: Why the human ruled this way.
    """

    review_id: CreativeDirectorReviewId
    status: ApprovalStatus
    rationale: str


@dataclass(frozen=True, slots=True)
class CommitteeBallot:
    """One committee member's verdict."""

    reviewer: str
    status: ApprovalStatus
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class CommitteeVote:
    """A committee's aggregated ruling on a review.

    Attributes:
        review_id: The review version being ruled on.
        ballots: The individual committee verdicts.
        require_unanimous: Whether approval requires every ballot to approve.
    """

    review_id: CreativeDirectorReviewId
    ballots: tuple[CommitteeBallot, ...]
    require_unanimous: bool = False
