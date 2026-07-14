"""The Customer Model — the consolidated portrait of who is being served.

:class:`CustomerModel` groups the outputs of customer synthesis — personas, the ICP,
jobs-to-be-done, the journey, and the psychology (pains, objections, motivations,
emotions) — into one cohesive, cited value object the report composes.

Pure domain: standard library and the customer sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from strategy.domain.customer.icp import IdealCustomerProfile
from strategy.domain.customer.journey import CustomerJourney
from strategy.domain.customer.jtbd import JTBDSet
from strategy.domain.customer.persona import PersonaSet
from strategy.domain.customer.psychology import (
    EmotionalTrigger,
    Objection,
    PainPoint,
    PurchaseMotivation,
)
from strategy.domain.shared.ids import StrategyEvidenceId

__all__ = ["CustomerModel"]


@dataclass(frozen=True, slots=True)
class CustomerModel:
    """The consolidated, cited customer portrait.

    Attributes:
        personas: The target personas.
        icp: The ideal customer profile.
        jobs: The jobs-to-be-done.
        journey: The customer journey.
        pains: The customer pains.
        objections: The purchase objections.
        motivations: The purchase motivations.
        emotions: The emotional triggers to activate.
    """

    icp: IdealCustomerProfile
    personas: PersonaSet = field(default_factory=PersonaSet)
    jobs: JTBDSet = field(default_factory=JTBDSet)
    journey: CustomerJourney = field(default_factory=CustomerJourney)
    pains: tuple[PainPoint, ...] = ()
    objections: tuple[Objection, ...] = ()
    motivations: tuple[PurchaseMotivation, ...] = ()
    emotions: tuple[EmotionalTrigger, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "pains", tuple(self.pains))
        object.__setattr__(self, "objections", tuple(self.objections))
        object.__setattr__(self, "motivations", tuple(self.motivations))
        object.__setattr__(self, "emotions", tuple(self.emotions))

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (
            *self.personas.evidence_ids(),
            *self.icp.evidence_ids,
            *self.jobs.evidence_ids(),
            *self.journey.evidence_ids(),
            *(eid for p in self.pains for eid in p.evidence_ids),
            *(eid for o in self.objections for eid in o.evidence_ids),
            *(eid for m in self.motivations for eid in m.evidence_ids),
            *(eid for e in self.emotions for eid in e.evidence_ids),
        )
