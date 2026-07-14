"""The Psychological Profile — the consolidated determination of the buying mind.

:class:`PsychologicalProfile` groups every determination the engine makes about the
customer's decision state — the target customer, their awareness and sophistication,
their intent, and the full set of motivations, anxieties, frictions, risks, trust
requirements, decision triggers, drivers, and confidence — into one cohesive, cited
value object the report composes.

Pure domain: standard library, the shared-kernel error base, and the state sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    AwarenessLevel,
    CustomerIntent,
    SophisticationLevel,
)
from psychology.domain.state.confidence import (
    DecisionTrigger,
    PurchaseConfidence,
    TrustRequirement,
)
from psychology.domain.state.drivers import Driver, PurchaseMotivation
from psychology.domain.state.friction import (
    PurchaseAnxiety,
    PurchaseFriction,
    RiskPerception,
)

__all__ = ["InvalidProfileError", "PsychologicalProfile"]


class InvalidProfileError(DesignDirectorError):
    """Raised when a psychological profile is constructed with invalid data."""

    code = "invalid_psychological_profile"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PsychologicalProfile:
    """The consolidated, cited determination of the customer's buying psychology.

    Attributes:
        target_customer: A one-line statement of who is deciding.
        awareness: The customer's awareness level.
        sophistication: The market's sophistication level.
        intent: The customer's purchase intent.
        confidence: The overall purchase-confidence picture.
        motivations: What motivates the purchase.
        anxieties: The anxieties in play.
        frictions: The frictions in the process.
        risks: The perceived risks.
        trust_requirements: What must be trusted before committing.
        decision_triggers: What moves the customer forward.
        drivers: The emotional/logical/social/urgency/retention drivers.
    """

    target_customer: str
    awareness: AwarenessLevel
    sophistication: SophisticationLevel
    intent: CustomerIntent
    confidence: PurchaseConfidence
    motivations: tuple[PurchaseMotivation, ...] = ()
    anxieties: tuple[PurchaseAnxiety, ...] = ()
    frictions: tuple[PurchaseFriction, ...] = ()
    risks: tuple[RiskPerception, ...] = ()
    trust_requirements: tuple[TrustRequirement, ...] = ()
    decision_triggers: tuple[DecisionTrigger, ...] = ()
    drivers: tuple[Driver, ...] = ()

    def __post_init__(self) -> None:
        if not self.target_customer or not self.target_customer.strip():
            raise InvalidProfileError("PsychologicalProfile.target_customer must be non-empty.")
        object.__setattr__(self, "motivations", tuple(self.motivations))
        object.__setattr__(self, "anxieties", tuple(self.anxieties))
        object.__setattr__(self, "frictions", tuple(self.frictions))
        object.__setattr__(self, "risks", tuple(self.risks))
        object.__setattr__(self, "trust_requirements", tuple(self.trust_requirements))
        object.__setattr__(self, "decision_triggers", tuple(self.decision_triggers))
        object.__setattr__(self, "drivers", tuple(self.drivers))

    def drivers_of(self, kind) -> tuple[Driver, ...]:
        return tuple(d for d in self.drivers if d.kind is kind)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return (
            *self.confidence.evidence_ids,
            *(eid for m in self.motivations for eid in m.evidence_ids),
            *(eid for a in self.anxieties for eid in a.evidence_ids),
            *(eid for f in self.frictions for eid in f.evidence_ids),
            *(eid for r in self.risks for eid in r.evidence_ids),
            *(eid for t in self.trust_requirements for eid in t.evidence_ids),
            *(eid for t in self.decision_triggers for eid in t.evidence_ids),
            *(eid for d in self.drivers for eid in d.evidence_ids),
        )
