"""Strategic decisions — the atomic, cited units of the strategy.

A :class:`StrategicDecision` is one resolved choice: what was decided, why, how
confident, how urgent, the alternatives considered, and the evidence it rests on.
Every section of the strategy is lifted into decisions so the whole strategy becomes a
single, traversable, auditable graph.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategicDecisionId, StrategyEvidenceId
from strategy.domain.shared.value_objects import (
    Confidence,
    ConsideredAlternative,
    DecisionType,
    Priority,
)

__all__ = ["InvalidDecisionError", "StrategicDecision"]


class InvalidDecisionError(DesignDirectorError):
    """Raised when a strategic decision is constructed with invalid data."""

    code = "invalid_strategic_decision"
    http_status = 422


@dataclass(frozen=True, slots=True)
class StrategicDecision:
    """One cited, prioritized strategic decision.

    Attributes:
        id: Decision identity.
        type: The strategic domain it belongs to.
        title: A short title.
        statement: The decision itself.
        rationale: Why it was made.
        confidence: Confidence in the decision.
        priority: Its priority.
        considered: The alternatives weighed and rejected (the trade-off record).
        evidence_ids: The evidence supporting it — must resolve in the report graph.
    """

    id: StrategicDecisionId
    type: DecisionType
    title: str
    statement: str
    confidence: Confidence
    priority: Priority
    rationale: str = ""
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidDecisionError("StrategicDecision.title must be non-empty.")
        if not self.statement or not self.statement.strip():
            raise InvalidDecisionError("StrategicDecision.statement must be non-empty.")
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
