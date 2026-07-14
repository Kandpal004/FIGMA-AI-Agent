"""Psychological drivers and motivations — what moves the decision forward.

A :class:`PurchaseMotivation` is a cited reason the customer wants to buy, mapped to the
Maslow need it serves. A :class:`Driver` is one of the five driver kinds (emotional,
logical, social, urgency, retention) with its strength. Together they model the positive
forces on the decision.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import DriverId, PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    DriverKind,
    Intensity,
    MaslowNeed,
)

__all__ = ["Driver", "InvalidDriverError", "PurchaseMotivation"]


class InvalidDriverError(DesignDirectorError):
    """Raised when a driver or motivation is constructed with invalid data."""

    code = "invalid_psychology_driver"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PurchaseMotivation:
    """A cited reason the customer wants to buy.

    Attributes:
        description: The motivation, in the customer's terms.
        maslow_need: The Maslow need it ultimately serves.
        intensity: How strong a motivator it is.
        evidence_ids: The evidence supporting it.
    """

    description: str
    maslow_need: MaslowNeed
    intensity: Intensity = Intensity(3)
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidDriverError("PurchaseMotivation.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Driver:
    """One cited psychological driver.

    Attributes:
        id: Driver identity.
        kind: The kind of driver (emotional/logical/social/urgency/retention).
        description: How the driver operates for this customer.
        intensity: How strong it is.
        evidence_ids: The evidence supporting it.
    """

    id: DriverId
    kind: DriverKind
    description: str
    intensity: Intensity = Intensity(3)
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidDriverError("Driver.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
