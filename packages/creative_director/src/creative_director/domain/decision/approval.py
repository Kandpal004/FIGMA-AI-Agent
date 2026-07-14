"""The ApprovalDecision — the Creative Director's ruling, recorded.

An :class:`ApprovalDecision` is the engine's binding verdict on a subject: the status, the
rationale, who decided (the system, a human Creative Director, or a committee), the overall
score it rested on, and the exact gates and blocking findings that drove it. It carries a
strong domain invariant — an ``APPROVED`` decision cannot cite a failing gate or a blocking
finding, so the platform can never approve something its own review says is broken.

Pure domain: standard library, the shared-kernel error base, CD ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from creative_director.domain.shared.ids import CDEvidenceId, DecisionId, FindingId
from creative_director.domain.shared.value_objects import (
    ApprovalStatus,
    DeciderRole,
    Score,
    ScoreCategory,
)

__all__ = ["ApprovalDecision", "InvalidApprovalError"]


class InvalidApprovalError(DesignDirectorError):
    """Raised when an approval decision is constructed inconsistently."""

    code = "invalid_creative_director_approval"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """The Creative Director's binding ruling on a subject.

    Attributes:
        id: Decision identity.
        status: The ruling.
        rationale: Why the ruling was made.
        decided_by: Who issued it.
        decided_at: When it was issued.
        overall_score: The overall score it rested on.
        failing_gates: The hard gates that failed (empty when approved).
        blocking_finding_ids: The blocking findings that drove it (empty when approved).
        superseded_by: The decision that later overrode this one, if any.
        evidence_ids: The evidence grounding the decision.
    """

    id: DecisionId
    status: ApprovalStatus
    rationale: str
    decided_by: DeciderRole
    decided_at: datetime
    overall_score: Score
    failing_gates: tuple[ScoreCategory, ...] = ()
    blocking_finding_ids: tuple[FindingId, ...] = ()
    superseded_by: DecisionId | None = None
    evidence_ids: tuple[CDEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise InvalidApprovalError("ApprovalDecision.rationale must be non-empty.")
        if self.status is ApprovalStatus.APPROVED and (
            self.failing_gates or self.blocking_finding_ids
        ):
            raise InvalidApprovalError(
                "An APPROVED decision cannot cite a failing gate or a blocking finding.",
                details={"failing_gates": [g.value for g in self.failing_gates]},
            )
        object.__setattr__(self, "failing_gates", tuple(dict.fromkeys(self.failing_gates)))
        object.__setattr__(self, "blocking_finding_ids", tuple(self.blocking_finding_ids))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def is_approved(self) -> bool:
        return self.status is ApprovalStatus.APPROVED

    @property
    def is_superseded(self) -> bool:
        return self.superseded_by is not None

    def all_evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return self.evidence_ids
