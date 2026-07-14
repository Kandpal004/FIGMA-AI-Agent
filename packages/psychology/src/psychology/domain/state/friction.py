"""Purchase friction — the anxieties, frictions, and risks that block the decision.

These cited value objects model the negative forces on the decision: the
:class:`PurchaseAnxiety` the customer feels, the :class:`PurchaseFriction` in the
process, and the :class:`RiskPerception` they weigh. Downstream UX/CRO must reduce
these; here they are diagnosed, not designed away.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    AnxietyKind,
    FrictionKind,
    Intensity,
    JourneyPhase,
    Likelihood,
    RiskKind,
)

__all__ = [
    "InvalidFrictionError",
    "PurchaseAnxiety",
    "PurchaseFriction",
    "RiskPerception",
]


class InvalidFrictionError(DesignDirectorError):
    """Raised when a friction value object is constructed with invalid data."""

    code = "invalid_purchase_friction"
    http_status = 422


def _require(value: str, field: str) -> None:
    if not value or not value.strip():
        raise InvalidFrictionError(f"{field} must be non-empty.")


@dataclass(frozen=True, slots=True)
class PurchaseAnxiety:
    """A cited anxiety the customer feels.

    Attributes:
        kind: The kind of anxiety.
        description: The anxiety in the customer's terms.
        intensity: How acute it is.
        phase: Where in the journey it bites.
        evidence_ids: The evidence supporting it.
    """

    kind: AnxietyKind
    description: str
    intensity: Intensity
    phase: JourneyPhase
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.description, "PurchaseAnxiety.description")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class PurchaseFriction:
    """A cited friction in the buying process.

    Attributes:
        kind: The kind of friction.
        description: What creates the friction.
        intensity: How much it slows the customer.
        phase: Where in the journey it occurs.
        evidence_ids: The evidence supporting it.
    """

    kind: FrictionKind
    description: str
    intensity: Intensity
    phase: JourneyPhase
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.description, "PurchaseFriction.description")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class RiskPerception:
    """A cited perceived risk the customer weighs.

    Attributes:
        kind: The kind of risk.
        description: The perceived risk.
        likelihood: How likely the customer feels it is.
        impact: How bad it would be (intensity).
        mitigation: The strategy to reduce the perception.
        evidence_ids: The evidence supporting it.
    """

    kind: RiskKind
    description: str
    likelihood: Likelihood
    impact: Intensity
    mitigation: str = ""
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.description, "RiskPerception.description")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def severity(self) -> int:
        """Likelihood × impact, in ``[1, 25]``."""
        return int(self.likelihood) * int(self.impact)
