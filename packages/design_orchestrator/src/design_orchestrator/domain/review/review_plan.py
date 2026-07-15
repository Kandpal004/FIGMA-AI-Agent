"""The review plan — the ordered checkpoints scheduled before Figma generation.

The orchestrator does not *run* reviews; it *schedules* them. A :class:`ReviewCheckpoint` is one
gate — tokens approved, layout approved, accessibility approved, performance approved, and the
final pre-generation sign-off — pinned to the execution stage it audits and grounded in the
Creative Director's evidence. A :class:`ReviewPlan` holds them in order and guarantees the final
``PRE_GENERATION`` gate is last: nothing reaches Figma generation until every prior gate and the
final sign-off are scheduled.

Pure domain: standard library, the shared-kernel error base, DO ids, evidence, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from design_orchestrator.domain.evidence.evidence import Citation
from design_orchestrator.domain.shared.ids import ReviewCheckpointId
from design_orchestrator.domain.shared.value_objects import (
    CheckpointStatus,
    ExecutionStepKind,
    ReviewGateKind,
)

__all__ = ["InvalidReviewPlanError", "ReviewCheckpoint", "ReviewPlan"]


class InvalidReviewPlanError(DesignDirectorError):
    """Raised when the review plan is constructed with invalid data."""

    code = "invalid_design_orchestrator_review_plan"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ReviewCheckpoint:
    """One scheduled gate before Figma generation.

    Attributes:
        id: Checkpoint identity.
        gate: Which gate this is.
        after_step: The execution stage this checkpoint audits.
        statement: The human-readable gate description.
        pass_criteria: The criteria that must hold to pass.
        status: The checkpoint status (always PENDING — the plan schedules, it does not run).
        citations: The evidence supporting this checkpoint (must resolve in the evidence graph).
    """

    id: ReviewCheckpointId
    gate: ReviewGateKind
    after_step: ExecutionStepKind
    statement: str
    pass_criteria: tuple[str, ...] = ()
    status: CheckpointStatus = CheckpointStatus.PENDING
    citations: tuple[Citation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidReviewPlanError(
                "ReviewCheckpoint.statement must be non-empty.", details={"gate": self.gate.value}
            )
        object.__setattr__(self, "statement", self.statement.strip())
        object.__setattr__(
            self,
            "pass_criteria",
            tuple(c.strip() for c in self.pass_criteria if c and c.strip()),
        )
        object.__setattr__(self, "citations", tuple(self.citations))

    @property
    def evidence_ids(self) -> tuple:
        return tuple(c.evidence_id for c in self.citations)


@dataclass(frozen=True, slots=True)
class ReviewPlan:
    """The ordered checkpoints, ending in the pre-generation sign-off."""

    checkpoints: tuple[ReviewCheckpoint, ...]

    def __post_init__(self) -> None:
        checkpoints = tuple(self.checkpoints)
        if not checkpoints:
            raise InvalidReviewPlanError(
                "A ReviewPlan must schedule at least the pre-generation gate."
            )
        gates = [c.gate for c in checkpoints]
        if len(set(gates)) != len(gates):
            raise InvalidReviewPlanError("Review gates must be unique.")
        if ReviewGateKind.PRE_GENERATION not in gates:
            raise InvalidReviewPlanError(
                "A ReviewPlan must include the PRE_GENERATION gate."
            )
        if checkpoints[-1].gate is not ReviewGateKind.PRE_GENERATION:
            raise InvalidReviewPlanError(
                "The PRE_GENERATION gate must be the last checkpoint."
            )
        object.__setattr__(self, "checkpoints", checkpoints)

    def __len__(self) -> int:
        return len(self.checkpoints)

    def __iter__(self):
        return iter(self.checkpoints)

    @property
    def gates(self) -> tuple[ReviewGateKind, ...]:
        return tuple(c.gate for c in self.checkpoints)

    @property
    def evidence_ids(self) -> tuple:
        return tuple(eid for c in self.checkpoints for eid in c.evidence_ids)
