"""The Trade-off model — a recorded tension resolved in the strategy.

Whenever a decision favours one option over a competing one — a prominent CTA over
brand restraint, density over whitespace — the engine records a :class:`TradeOff`:
what was chosen, what was sacrificed, why, and the evidence behind the call. This
makes the strategy's compromises explicit and auditable, and it is the raw material
from which alternative strategies are described.

Pure domain: standard library, the shared-kernel error base, and reasoning ids.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import DecisionNodeId, EvidenceId, TradeOffId
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = ["InvalidTradeOffError", "TradeOff"]


class InvalidTradeOffError(DesignDirectorError):
    """Raised when a trade-off is constructed with invalid data."""

    code = "invalid_tradeoff"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TradeOff:
    """A tension between competing options, and how it was resolved.

    Attributes:
        id: Trade-off identity.
        dimension: The dimension the tension sits in.
        chosen: The option that prevailed.
        sacrificed: The option that yielded.
        rationale: Why the call was made.
        decision_id: The decision this trade-off arose from, if any.
        evidence_ids: The evidence behind the resolution.
    """

    id: TradeOffId
    dimension: ReasoningDimension
    chosen: str
    sacrificed: str
    rationale: str
    decision_id: DecisionNodeId | None = None
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("chosen", self.chosen),
            ("sacrificed", self.sacrificed),
            ("rationale", self.rationale),
        ):
            if not value or not value.strip():
                raise InvalidTradeOffError(f"TradeOff.{name} must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
