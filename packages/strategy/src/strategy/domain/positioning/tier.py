"""Positioning tier & statement — the single most consequential strategic choice.

The :class:`StrategyTier` (Luxury / Premium / Affordable / Enterprise / Technical /
Minimal) sets the register for every downstream decision. A :class:`PositioningStatement`
captures the classic Moore template — *for* a customer *who* has a need, the brand
*is* a category that *delivers* a benefit, *unlike* the alternative, *because* of a
reason to believe — and records the tiers it considered and rejected.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import (
    Confidence,
    ConsideredAlternative,
    StrategyTier,
)

__all__ = ["InvalidPositioningStatementError", "PositioningStatement"]


class InvalidPositioningStatementError(DesignDirectorError):
    """Raised when a positioning statement is constructed with invalid data."""

    code = "invalid_positioning_statement"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PositioningStatement:
    """The cited, tier-anchored positioning statement.

    Attributes:
        tier: The committed positioning tier.
        for_customer: The target customer ("For …").
        need: The need or opportunity ("who …").
        category: The category the brand competes in ("the brand is a …").
        benefit: The key benefit ("that …").
        unlike: The primary alternative it is positioned against ("unlike …").
        reason_to_believe: Why the promise is credible ("because …").
        confidence: Confidence in the positioning.
        considered: Tiers/positions weighed and rejected.
        evidence_ids: The evidence supporting it.
    """

    tier: StrategyTier
    for_customer: str
    need: str
    category: str
    benefit: str
    confidence: Confidence
    unlike: str = ""
    reason_to_believe: str = ""
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("for_customer", "need", "category", "benefit"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise InvalidPositioningStatementError(
                    f"PositioningStatement.{name} must be non-empty."
                )
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def statement(self) -> str:
        """The canonical one-paragraph positioning statement."""
        text = (
            f"For {self.for_customer} who {self.need}, {self.category} "
            f"delivers {self.benefit}"
        )
        if self.unlike:
            text += f", unlike {self.unlike}"
        if self.reason_to_believe:
            text += f", because {self.reason_to_believe}"
        return text + "."
