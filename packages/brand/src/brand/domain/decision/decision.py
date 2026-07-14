"""Brand decisions — the atomic, cited units of the brand strategy.

A :class:`BrandDecision` is one resolved brand choice: what was decided, why, how
confident, how urgent, the alternatives considered, and the evidence it rests on. Every
element of the brand — identity, personality, creative direction, verbal system — is
lifted into decisions so the whole brand becomes a single, traversable, auditable graph.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandDecisionId, BrandEvidenceId
from brand.domain.shared.value_objects import (
    BrandDecisionType,
    Confidence,
    ConsideredAlternative,
    Priority,
)

__all__ = ["BrandDecision", "InvalidDecisionError"]


class InvalidDecisionError(DesignDirectorError):
    """Raised when a brand decision is constructed with invalid data."""

    code = "invalid_brand_decision"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandDecision:
    """One cited, prioritized brand decision.

    Attributes:
        id: Decision identity.
        type: The brand domain it belongs to.
        title: A short title.
        statement: The decision itself.
        rationale: Why it was made.
        confidence: Confidence in the decision.
        priority: Its priority.
        considered: The alternatives weighed and rejected (the trade-off record).
        evidence_ids: The evidence supporting it — must resolve in the report graph.
    """

    id: BrandDecisionId
    type: BrandDecisionType
    title: str
    statement: str
    confidence: Confidence
    priority: Priority
    rationale: str = ""
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidDecisionError("BrandDecision.title must be non-empty.")
        if not self.statement or not self.statement.strip():
            raise InvalidDecisionError("BrandDecision.statement must be non-empty.")
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
