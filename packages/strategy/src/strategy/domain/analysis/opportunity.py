"""Business & revenue opportunities — where the upside is.

A :class:`BusinessOpportunity` names a cited upside with an impact and confidence; a
:class:`RevenueOpportunity` sharpens it into an expected monetary value with the lever
that unlocks it and the assumptions behind the estimate. The :class:`OpportunityRegister`
holds both and totals the addressable revenue.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import (
    BusinessOpportunityId,
    RevenueOpportunityId,
    StrategyEvidenceId,
)
from strategy.domain.shared.value_objects import (
    Confidence,
    ImpactScore,
    Money,
    OpportunityCategory,
)

__all__ = [
    "BusinessOpportunity",
    "InvalidOpportunityError",
    "OpportunityRegister",
    "RevenueOpportunity",
]


class InvalidOpportunityError(DesignDirectorError):
    """Raised when an opportunity is constructed with invalid data."""

    code = "invalid_opportunity"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BusinessOpportunity:
    """One cited business opportunity.

    Attributes:
        id: Opportunity identity.
        category: The opportunity category.
        description: What the opportunity is.
        impact: Its estimated impact (1–5).
        confidence: Confidence in the opportunity.
        evidence_ids: The evidence supporting it.
    """

    id: BusinessOpportunityId
    category: OpportunityCategory
    description: str
    impact: ImpactScore
    confidence: Confidence
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidOpportunityError("BusinessOpportunity.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class RevenueOpportunity:
    """One cited revenue opportunity with an expected monetary value.

    Attributes:
        id: Opportunity identity.
        category: The opportunity category.
        description: What the opportunity is.
        expected_value: The expected annual value if captured.
        confidence: Confidence in the estimate.
        lever: The strategic lever that unlocks it.
        assumptions: The assumptions behind the estimate.
        evidence_ids: The evidence supporting it.
    """

    id: RevenueOpportunityId
    category: OpportunityCategory
    description: str
    expected_value: Money
    confidence: Confidence
    lever: str = ""
    assumptions: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidOpportunityError("RevenueOpportunity.description must be non-empty.")
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def risk_adjusted_value(self) -> Money:
        """The expected value discounted by the confidence in it."""
        return Money(
            amount=round(self.expected_value.amount * self.confidence.value, 2),
            currency=self.expected_value.currency,
        )


@dataclass(frozen=True, slots=True)
class OpportunityRegister:
    """An immutable register of business and revenue opportunities."""

    business: tuple[BusinessOpportunity, ...] = ()
    revenue: tuple[RevenueOpportunity, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "business", tuple(self.business))
        object.__setattr__(self, "revenue", tuple(self.revenue))

    @classmethod
    def of(
        cls,
        *,
        business: Iterable[BusinessOpportunity] = (),
        revenue: Iterable[RevenueOpportunity] = (),
    ) -> OpportunityRegister:
        return cls(business=tuple(business), revenue=tuple(revenue))

    def total_revenue_potential(self, currency: str = "USD") -> Money:
        """The sum of risk-adjusted revenue opportunities in ``currency``.

        Only opportunities already denominated in ``currency`` are summed; mixed
        currencies are not silently converted.
        """
        total = sum(
            o.risk_adjusted_value.amount
            for o in self.revenue
            if o.expected_value.currency == currency.strip().upper()
        )
        return Money(amount=round(total, 2), currency=currency)

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (
            *(eid for o in self.business for eid in o.evidence_ids),
            *(eid for o in self.revenue for eid in o.evidence_ids),
        )
