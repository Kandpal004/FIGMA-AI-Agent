"""CreativeDirectorReview — the aggregate the whole engine produces.

An immutable, versioned review: the subject and policy, the sixteen dimension reviews, the
scorecard, the binding approval decision, the decision history, the quality and improvement
matrices, the five graphs, and the review's own quality picture. It is the platform's final
authority — ``can_proceed`` is the single go/no-go signal every downstream phase obeys.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any dimension review, finding,
   required change, score, approval decision, or graph node must resolve in the review's
   :class:`EvidenceGraph`. No ruling the engine cannot cite can be built — there are no
   ungrounded approvals and no ungrounded rejections.
2. **Decision integrity** — the approval decision is consistent with the scorecard and the
   active policy: ``APPROVED`` is impossible when the overall score is below the effective
   threshold, when any hard gate fails, or when any dimension carries a blocking finding; a
   non-approval must be justified by a failing gate, a blocker, or a sub-threshold overall;
   and the recorded overall must equal the scorecard's overall. The current decision must be
   the head of the decision history.
3. **Graph integrity** — every review graph is acyclic and resolves (enforced by the graph
   primitive), and each dimension is reviewed at most once.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–12: a
re-review, a human override, or a committee ruling mints a new version under the same lineage,
and the decision history is retained.

Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from creative_director.domain.context.context import ReviewSubject
from creative_director.domain.decision.approval import ApprovalDecision
from creative_director.domain.decision.history import DecisionHistory
from creative_director.domain.evidence.evidence import EvidenceGraph
from creative_director.domain.graph.graphs import CreativeDirectorGraphs
from creative_director.domain.matrix.improvement_matrix import ImprovementMatrix
from creative_director.domain.matrix.quality_matrix import QualityMatrix
from creative_director.domain.policy.policy import ReviewPolicy
from creative_director.domain.quality.quality import ReviewQualityMetrics
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.ids import (
    CDEvidenceId,
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)
from creative_director.domain.shared.value_objects import (
    ApprovalStatus,
    DeciderRole,
    ReviewDimension,
    ScoreCategory,
)

__all__ = ["CreativeDirectorReview", "InvalidReviewError"]

_EPSILON = 0.01


class InvalidReviewError(DesignDirectorError):
    """Raised when a review violates an integrity invariant."""

    code = "invalid_creative_director_review"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CreativeDirectorReview:
    """The complete, provenance-tracked, versioned Creative Director review."""

    id: CreativeDirectorReviewId
    lineage_id: CreativeDirectorReviewLineageId
    version: int
    project_id: str
    subject: ReviewSubject
    policy: ReviewPolicy
    dimension_reviews: tuple[DimensionReview, ...]
    scorecard: Scorecard
    approval: ApprovalDecision
    decision_history: DecisionHistory
    quality_matrix: QualityMatrix
    improvement_matrix: ImprovementMatrix
    graphs: CreativeDirectorGraphs
    evidence_graph: EvidenceGraph
    quality: ReviewQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidReviewError(
                "CreativeDirectorReview.version must be >= 1.", details={"version": self.version}
            )
        if not self.dimension_reviews:
            raise InvalidReviewError("A review must cover at least one dimension.")
        self._validate_unique_dimensions()
        self._validate_provenance()
        self._validate_decision()

    # -- invariants -------------------------------------------------------- #
    def _validate_unique_dimensions(self) -> None:
        seen: set[ReviewDimension] = set()
        for dr in self.dimension_reviews:
            if dr.dimension in seen:
                raise InvalidReviewError(
                    "A dimension is reviewed more than once.",
                    details={"dimension": dr.dimension.value},
                )
            seen.add(dr.dimension)

    def _referenced_evidence(self) -> set[CDEvidenceId]:
        referenced: set[CDEvidenceId] = set()
        for dr in self.dimension_reviews:
            referenced.update(dr.all_evidence_ids())
        referenced.update(self.scorecard.evidence_ids())
        referenced.update(self.approval.all_evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        for change in self.improvement_matrix:
            referenced.update(change.all_evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidReviewError(
                "Review references evidence absent from its evidence graph "
                "(no ungrounded rulings).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def failing_gates(self) -> tuple[ScoreCategory, ...]:
        """Hard-gated categories whose score is below the profile's minimum."""
        failing: list[ScoreCategory] = []
        for category, minimum in self.policy.profile.hard_gates.items():
            cs = self.scorecard.get(category)
            if cs is not None and cs.score.value < minimum.value:
                failing.append(category)
        return tuple(failing)

    def has_blocking_finding(self) -> bool:
        return any(dr.has_blocker for dr in self.dimension_reviews)

    def _validate_decision(self) -> None:
        if abs(self.approval.overall_score.value - self.scorecard.overall.value) > _EPSILON:
            raise InvalidReviewError(
                "Approval overall score must equal the scorecard overall.",
                details={"approval": self.approval.overall_score.value,
                         "scorecard": self.scorecard.overall.value},
            )
        failing = self.failing_gates()
        blocked = self.has_blocking_finding()
        below_threshold = (
            self.scorecard.overall.value < self.policy.effective_threshold.value
        )
        if self.approval.is_approved:
            if failing:
                raise InvalidReviewError(
                    "Cannot APPROVE with a failing hard gate.",
                    details={"failing_gates": [g.value for g in failing]},
                )
            if blocked:
                raise InvalidReviewError("Cannot APPROVE with a blocking finding.")
            if below_threshold:
                raise InvalidReviewError(
                    "Cannot APPROVE below the effective threshold.",
                    details={"overall": self.scorecard.overall.value,
                             "threshold": self.policy.effective_threshold.value},
                )
        elif (
            self.approval.decided_by is DeciderRole.SYSTEM
            and self.approval.status in (
                ApprovalStatus.REJECTED,
                ApprovalStatus.CHANGES_REQUESTED,
            )
        ):
            # The automatic (system) decision must be justified by something concrete.
            # A human or committee holds veto authority — their rationale suffices — and
            # ESCALATED is a deferral to a human, so neither needs score justification.
            if not (failing or blocked or below_threshold):
                raise InvalidReviewError(
                    "An automatic rejection or change request must cite a failing gate, a "
                    "blocker, or a sub-threshold overall.",
                    details={"status": self.approval.status.value},
                )
        current = self.decision_history.current()
        if current is None or current.decision_id != self.approval.id:
            raise InvalidReviewError(
                "The current decision must head the decision history.",
                details={"decision_id": str(self.approval.id)},
            )

    # -- queries ----------------------------------------------------------- #
    def dimension_count(self) -> int:
        return len(self.dimension_reviews)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_approved(self) -> bool:
        return self.approval.is_approved

    @property
    def can_proceed(self) -> bool:
        """The platform's go/no-go signal: approved, fully grounded, and evidence-backed."""
        return (
            self.approval.is_approved
            and self.quality.is_fully_grounded
            and not self.has_blocking_finding()
            and self.evidence_count() > 0
        )
