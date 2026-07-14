"""Pricing, offer & urgency strategy — the commercial signals.

A :class:`PricingStrategy` sets the posture and the :class:`PricingSignal` s the
experience should communicate; an :class:`OfferStrategy` frames the offers; an
:class:`UrgencyStrategy` decides urgency — always with an honesty guardrail, since
urgency must be evidence-justified and never a dark pattern.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import (
    PricingPosture,
    PricingSignalKind,
    UrgencyKind,
)

__all__ = [
    "InvalidPricingError",
    "OfferStrategy",
    "PricingSignal",
    "PricingStrategy",
    "UrgencyStrategy",
]


class InvalidPricingError(DesignDirectorError):
    """Raised when pricing strategy is constructed with invalid data."""

    code = "invalid_pricing_strategy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PricingSignal:
    """One cited pricing signal.

    Attributes:
        kind: The kind of pricing signal.
        rationale: Why it fits the strategy.
        evidence_ids: The evidence supporting it.
    """

    kind: PricingSignalKind
    rationale: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class OfferStrategy:
    """The cited approach to offers.

    Attributes:
        offers: The offer types to run (strategy, not campaigns).
        framing: How offers should be framed to fit the tier.
        evidence_ids: The evidence supporting it.
    """

    offers: tuple[str, ...] = ()
    framing: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "offers", tuple(self.offers))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class UrgencyStrategy:
    """The cited urgency approach, with an honesty guardrail.

    Attributes:
        kinds: The kinds of urgency to use.
        honesty_guardrail: The rule that keeps urgency truthful (no dark patterns).
        evidence_ids: The evidence supporting it.
    """

    kinds: tuple[UrgencyKind, ...] = ()
    honesty_guardrail: str = (
        "Urgency must reflect real conditions; no fabricated scarcity or countdowns."
    )
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kinds", tuple(self.kinds))
        if not self.honesty_guardrail or not self.honesty_guardrail.strip():
            raise InvalidPricingError("UrgencyStrategy.honesty_guardrail must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class PricingStrategy:
    """The complete, cited pricing/offer/urgency strategy."""

    posture: PricingPosture
    signals: tuple[PricingSignal, ...] = ()
    offer: OfferStrategy = OfferStrategy()
    urgency: UrgencyStrategy = UrgencyStrategy()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (
            *self.evidence_ids,
            *self.offer.evidence_ids,
            *self.urgency.evidence_ids,
            *(eid for s in self.signals for eid in s.evidence_ids),
        )
