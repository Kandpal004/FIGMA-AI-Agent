"""Stage — Approval Evaluation.

Turns the scorecard, the findings, and the policy into a binding :class:`ApprovalDecision`,
deterministically. Hard gates are checked first (any failing gate blocks approval), then
blocking findings (any blocker rejects), then the overall threshold (below ⇒ changes
requested). The review mode then arbitrates: ``AUTOMATIC`` and ``CREATIVE_DIRECTOR_OVERRIDE``
let the computed status stand (a human may later supersede an override); ``HUMAN_ASSISTED``
and ``REVIEW_COMMITTEE`` defer to a human by escalating, carrying the computed recommendation
in the rationale.

Pure application: standard library and the domain models.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from creative_director.domain.decision.approval import ApprovalDecision
from creative_director.domain.policy.policy import ReviewPolicy
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.ids import DecisionId, FindingId
from creative_director.domain.shared.value_objects import (
    ApprovalStatus,
    DeciderRole,
    ReviewMode,
    ScoreCategory,
)

__all__ = ["ApprovalEvaluator"]

_DEFERRING_MODES = (ReviewMode.HUMAN_ASSISTED, ReviewMode.REVIEW_COMMITTEE)


class ApprovalEvaluator:
    """Computes the Creative Director's binding decision from scores, findings, and policy."""

    def evaluate(
        self,
        scorecard: Scorecard,
        dimension_reviews: Sequence[DimensionReview],
        policy: ReviewPolicy,
        now: datetime,
    ) -> ApprovalDecision:
        failing = self._failing_gates(scorecard, policy)
        blockers = tuple(
            f.id for dr in dimension_reviews for f in dr.blocking_findings()
        )
        overall = scorecard.overall
        below_threshold = overall.value < policy.effective_threshold.value

        computed, rationale = self._computed(failing, blockers, below_threshold, overall.value,
                                              policy.effective_threshold.value)

        if policy.mode in _DEFERRING_MODES:
            status = ApprovalStatus.ESCALATED
            rationale = f"Escalated for human decision; recommendation: {computed.value}. {rationale}"
        else:
            status = computed

        evidence = scorecard.get(ScoreCategory.OVERALL)
        return ApprovalDecision(
            id=DecisionId.new(), status=status, rationale=rationale,
            decided_by=DeciderRole.SYSTEM, decided_at=now, overall_score=overall,
            failing_gates=failing if status is not ApprovalStatus.APPROVED else (),
            blocking_finding_ids=blockers if status is not ApprovalStatus.APPROVED else (),
            evidence_ids=(evidence.evidence_ids if evidence is not None else ()),
        )

    @staticmethod
    def _failing_gates(
        scorecard: Scorecard, policy: ReviewPolicy
    ) -> tuple[ScoreCategory, ...]:
        failing: list[ScoreCategory] = []
        for category, minimum in policy.profile.hard_gates.items():
            cs = scorecard.get(category)
            if cs is not None and cs.score.value < minimum.value:
                failing.append(category)
        return tuple(failing)

    @staticmethod
    def _computed(
        failing: tuple[ScoreCategory, ...],
        blockers: tuple[FindingId, ...],
        below_threshold: bool,
        overall: float,
        threshold: float,
    ) -> tuple[ApprovalStatus, str]:
        if blockers:
            return (
                ApprovalStatus.REJECTED,
                f"Rejected: {len(blockers)} blocking issue(s) must be resolved.",
            )
        if failing:
            gates = ", ".join(g.value for g in failing)
            return (
                ApprovalStatus.CHANGES_REQUESTED,
                f"Changes requested: hard gate(s) below minimum — {gates}.",
            )
        if below_threshold:
            return (
                ApprovalStatus.CHANGES_REQUESTED,
                f"Changes requested: overall {overall:.1f} is below the threshold {threshold:.1f}.",
            )
        return (
            ApprovalStatus.APPROVED,
            f"Approved: overall {overall:.1f} meets the threshold {threshold:.1f} with no "
            f"failing gates or blockers.",
        )
