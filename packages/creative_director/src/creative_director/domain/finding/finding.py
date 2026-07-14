"""The Finding and RequiredChange models — the atoms of a review verdict.

A :class:`Finding` is one observation the Creative Director makes about a dimension: a
blocking issue, a warning, or a recommendation, optionally naming the design
:class:`AntiPattern` it represents (a generic layout, weak hierarchy, low trust, a generic AI
pattern, …). A :class:`RequiredChange` is a concrete, prioritised fix the review demands
before a subject can pass. Both cite the evidence that justifies them — an ungrounded
criticism carries no authority.

Pure domain: standard library, the shared-kernel error base, CD ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.shared.ids import CDEvidenceId, FindingId, RequiredChangeId
from creative_director.domain.shared.value_objects import (
    AntiPattern,
    FindingSeverity,
    Priority,
    ReviewDimension,
)

__all__ = ["Finding", "InvalidFindingError", "RequiredChange"]


class InvalidFindingError(DesignDirectorError):
    """Raised when a finding or required change is constructed with invalid data."""

    code = "invalid_creative_director_finding"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Finding:
    """One observation the Creative Director raises about a dimension.

    Attributes:
        id: Finding identity.
        dimension: The review dimension it concerns.
        severity: Whether it blocks approval, warns, or merely recommends.
        statement: The observation, phrased so it can be acted on.
        anti_pattern: The design anti-pattern it represents, if any.
        evidence_ids: The evidence grounding the finding.
    """

    id: FindingId
    dimension: ReviewDimension
    severity: FindingSeverity
    statement: str
    anti_pattern: AntiPattern | None = None
    evidence_ids: tuple[CDEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidFindingError("Finding.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def is_blocking(self) -> bool:
        return self.severity is FindingSeverity.BLOCKING

    def all_evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class RequiredChange:
    """A concrete fix the review demands before a subject can pass.

    Attributes:
        id: Change identity.
        dimension: The dimension the change addresses.
        description: What must change.
        priority: How urgent the change is (5 = highest).
        impact: The expected impact of making the change (1–5).
        blocking: Whether the change blocks approval until resolved.
        evidence_ids: The evidence grounding the change.
    """

    id: RequiredChangeId
    dimension: ReviewDimension
    description: str
    priority: Priority = Priority(3)
    impact: Priority = Priority(3)
    blocking: bool = False
    evidence_ids: tuple[CDEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidFindingError("RequiredChange.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def rank(self) -> int:
        """A combined urgency used to order the improvement matrix (higher first)."""
        return int(self.priority) * int(self.impact)

    def all_evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return self.evidence_ids
