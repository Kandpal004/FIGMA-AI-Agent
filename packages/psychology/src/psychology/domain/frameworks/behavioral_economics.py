"""Behavioral economics — the persuasion principles, applied ethically.

A :class:`BehavioralPrinciple` records how one Cialdini/behavioral-economics principle
(loss aversion, anchoring, scarcity, social proof, authority, commitment, reciprocity,
choice architecture, peak-end) applies to this customer — and, crucially, the **ethical
guardrail** that keeps its use honest. Scarcity and urgency must reflect real conditions;
no dark patterns.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import BehavioralPrincipleKind

__all__ = ["BehavioralPrinciple", "BehavioralPrincipleSet", "InvalidPrincipleError"]


class InvalidPrincipleError(DesignDirectorError):
    """Raised when a behavioral principle is constructed with invalid data."""

    code = "invalid_behavioral_principle"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BehavioralPrinciple:
    """One cited, ethically-guarded application of a behavioral principle.

    Attributes:
        kind: The principle being applied.
        application: Where and how it applies for this customer.
        ethical_guardrail: The rule that keeps its use honest (no dark patterns).
        evidence_ids: The evidence supporting it.
    """

    kind: BehavioralPrincipleKind
    application: str
    ethical_guardrail: str = "Use must reflect reality; never fabricate scarcity or proof."
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.application or not self.application.strip():
            raise InvalidPrincipleError("BehavioralPrinciple.application must be non-empty.")
        if not self.ethical_guardrail or not self.ethical_guardrail.strip():
            raise InvalidPrincipleError("BehavioralPrinciple.ethical_guardrail must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BehavioralPrincipleSet:
    """An immutable set of applied behavioral principles."""

    principles: tuple[BehavioralPrinciple, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))

    @classmethod
    def of(cls, principles: Iterable[BehavioralPrinciple]) -> BehavioralPrincipleSet:
        return cls(principles=tuple(principles))

    def __len__(self) -> int:
        return len(self.principles)

    def __iter__(self):
        return iter(self.principles)

    def kinds(self) -> frozenset[BehavioralPrincipleKind]:
        return frozenset(p.kind for p in self.principles)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for p in self.principles for eid in p.evidence_ids)
