"""Purchase confidence — the trust requirements and triggers that unlock the decision.

These cited value objects model what the customer needs before they will commit: the
:class:`TrustRequirement` s they must have satisfied, the :class:`DecisionTrigger` s that
move them forward, and the overall :class:`PurchaseConfidence` picture.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import (
    DecisionTriggerId,
    PsychologyEvidenceId,
    TrustRequirementId,
)
from psychology.domain.shared.value_objects import (
    DriverKind,
    Intensity,
    JourneyPhase,
    Priority,
    TrustRequirementKind,
)

__all__ = [
    "DecisionTrigger",
    "InvalidConfidenceError",
    "PurchaseConfidence",
    "TrustRequirement",
]


class InvalidConfidenceError(DesignDirectorError):
    """Raised when a confidence value object is constructed with invalid data."""

    code = "invalid_purchase_confidence"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TrustRequirement:
    """A cited trust the customer must have satisfied before committing.

    Attributes:
        id: Requirement identity.
        kind: The kind of trust required.
        description: What must be true for the customer to trust.
        phase: The journey phase where it matters most.
        priority: Its priority relative to other trust requirements.
        evidence_ids: The evidence supporting it.
    """

    id: TrustRequirementId
    kind: TrustRequirementKind
    description: str
    phase: JourneyPhase
    priority: Priority = Priority(3)
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidConfidenceError("TrustRequirement.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class DecisionTrigger:
    """A cited moment or condition that moves the customer forward.

    Attributes:
        id: Trigger identity.
        description: What the trigger is.
        activates: The driver kind it activates.
        phase: The journey phase where it fires.
        evidence_ids: The evidence supporting it.
    """

    id: DecisionTriggerId
    description: str
    activates: DriverKind
    phase: JourneyPhase
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidConfidenceError("DecisionTrigger.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class PurchaseConfidence:
    """The cited overall purchase-confidence picture.

    Attributes:
        level: How confident the customer currently is (1–5).
        boosters: What raises confidence.
        blockers: What lowers confidence.
        evidence_ids: The evidence supporting it.
    """

    level: Intensity
    boosters: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "boosters", tuple(self.boosters))
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
