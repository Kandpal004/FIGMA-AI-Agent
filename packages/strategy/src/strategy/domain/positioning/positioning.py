"""Positioning strategy — brand, customer, and visual positioning.

The :class:`PositioningStrategy` aggregates the tier-anchored
:class:`PositioningStatement` with three cited facets:

* :class:`BrandPositioning` — how the brand wants to be perceived in the market.
* :class:`CustomerPositioning` — the customer's frame: the alternative they compare
  against and the shift the brand asks them to make.
* :class:`VisualPositioning` — the *strategic intent* for the visual system
  (adjectives, design principles, references to avoid). It states intent only; it does
  **not** emit colours, typography, or layout — that translation is a later phase.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.positioning.tier import PositioningStatement
from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import StrategyTier

__all__ = [
    "BrandPositioning",
    "CustomerPositioning",
    "InvalidPositioningError",
    "PositioningStrategy",
    "VisualPositioning",
]


class InvalidPositioningError(DesignDirectorError):
    """Raised when positioning is constructed with invalid data."""

    code = "invalid_positioning"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandPositioning:
    """How the brand wants to be perceived.

    Attributes:
        perception: The perception the brand aims for.
        market_frame: The market it wants to own a place in.
        differentiators: What sets it apart.
        evidence_ids: The evidence supporting it.
    """

    perception: str
    market_frame: str = ""
    differentiators: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.perception or not self.perception.strip():
            raise InvalidPositioningError("BrandPositioning.perception must be non-empty.")
        object.__setattr__(self, "differentiators", tuple(self.differentiators))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class CustomerPositioning:
    """The customer's frame of reference.

    Attributes:
        current_alternative: What the customer does/uses today.
        desired_shift: The shift the brand asks them to make.
        gains: The gains they get by shifting.
        evidence_ids: The evidence supporting it.
    """

    current_alternative: str
    desired_shift: str
    gains: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.current_alternative or not self.current_alternative.strip():
            raise InvalidPositioningError(
                "CustomerPositioning.current_alternative must be non-empty."
            )
        if not self.desired_shift or not self.desired_shift.strip():
            raise InvalidPositioningError(
                "CustomerPositioning.desired_shift must be non-empty."
            )
        object.__setattr__(self, "gains", tuple(self.gains))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class VisualPositioning:
    """The strategic intent for the visual system — intent only, never UI.

    Attributes:
        tier: The tier the visual system must express.
        adjectives: The adjectives the visual language should evoke.
        design_principles: Strategic design principles (e.g. "restraint over density").
        references_to_avoid: Anti-patterns the visual system must avoid.
        evidence_ids: The evidence supporting it.
    """

    tier: StrategyTier
    adjectives: tuple[str, ...] = ()
    design_principles: tuple[str, ...] = ()
    references_to_avoid: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "adjectives", tuple(self.adjectives))
        object.__setattr__(self, "design_principles", tuple(self.design_principles))
        object.__setattr__(self, "references_to_avoid", tuple(self.references_to_avoid))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class PositioningStrategy:
    """The complete, tier-anchored positioning."""

    statement: PositioningStatement
    brand: BrandPositioning
    customer: CustomerPositioning
    visual: VisualPositioning

    @property
    def tier(self) -> StrategyTier:
        return self.statement.tier

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (
            *self.statement.evidence_ids,
            *self.brand.evidence_ids,
            *self.customer.evidence_ids,
            *self.visual.evidence_ids,
        )
