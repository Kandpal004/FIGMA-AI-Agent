"""Buying personas — the decision-role lens on the customer.

Where a :class:`~psychology.domain.persona.persona.CustomerPersona` says *who* the
customer is, a :class:`BuyingPersona` says *how they decide*: the role they play in the
purchase, what they must come to believe before they will proceed, and what blocks them.
This is the behavioral, decision-centric persona CRO actually acts on.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import BuyingPersonaId, PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    AwarenessLevel,
    BuyingRole,
    SophisticationLevel,
)

__all__ = ["BuyingPersona", "BuyingPersonaSet", "InvalidBuyingPersonaError"]


class InvalidBuyingPersonaError(DesignDirectorError):
    """Raised when a buying persona is constructed with invalid data."""

    code = "invalid_buying_persona"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BuyingPersona:
    """A cited, decision-role portrait of the customer.

    Attributes:
        id: Persona identity.
        name: A memorable name.
        role: The role this persona plays in the buying decision.
        awareness: The awareness level they enter at.
        sophistication: The market sophistication they bring.
        must_believe: What they must come to believe before proceeding.
        blocked_by: What blocks them from proceeding.
        decision_criteria: The criteria they judge the offer against.
        evidence_ids: The evidence supporting it.
    """

    id: BuyingPersonaId
    name: str
    role: BuyingRole
    awareness: AwarenessLevel
    sophistication: SophisticationLevel
    must_believe: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    decision_criteria: tuple[str, ...] = ()
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidBuyingPersonaError("BuyingPersona.name must be non-empty.")
        object.__setattr__(self, "must_believe", tuple(self.must_believe))
        object.__setattr__(self, "blocked_by", tuple(self.blocked_by))
        object.__setattr__(self, "decision_criteria", tuple(self.decision_criteria))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BuyingPersonaSet:
    """An immutable set of buying personas."""

    personas: tuple[BuyingPersona, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "personas", tuple(self.personas))

    @classmethod
    def of(cls, personas: Iterable[BuyingPersona]) -> BuyingPersonaSet:
        return cls(personas=tuple(personas))

    def __len__(self) -> int:
        return len(self.personas)

    def __iter__(self):
        return iter(self.personas)

    def by_role(self, role: BuyingRole) -> tuple[BuyingPersona, ...]:
        return tuple(p for p in self.personas if p.role is role)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for p in self.personas for eid in p.evidence_ids)
