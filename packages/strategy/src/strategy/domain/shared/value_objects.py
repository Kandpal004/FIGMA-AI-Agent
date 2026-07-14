"""Shared value objects for the Business Strategy Engine.

These immutable, self-validating value objects are the vocabulary the engine reasons
in: the provenance of the evidence it cites, the positioning tiers it can choose, the
kinds of decision it makes and the typed edges between them, the psychological and
commercial primitives of ecommerce strategy, and the calibrated scales it scores
everything on.

Everything here is pure domain: only the standard library and the shared-kernel error
base (:mod:`core.errors`). No framework, no I/O, no global mutable state, and no
import of any provider or other engine — those are reached only through ports,
keeping this domain independent.

Testing considerations
----------------------
* :class:`StrategyTier` has exactly six members (Luxury/Premium/Affordable/
  Enterprise/Technical/Minimal).
* :class:`Confidence`, :class:`StrategyScore`, :class:`Percentage`,
  :class:`ImpactScore`, :class:`EffortScore`, and :class:`ReachScore` validate their
  ranges, order by value, and (where relevant) derive bands.
* :class:`Money` rejects negative amounts and normalises its currency code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "Confidence",
    "ConsideredAlternative",
    "DecisionRelation",
    "DecisionType",
    "EffortScore",
    "EmotionKind",
    "GoalCategory",
    "GoalHorizon",
    "ImpactScore",
    "InvalidStrategyValueError",
    "JourneyPhase",
    "JobType",
    "Likelihood",
    "MessagingTone",
    "Money",
    "OpportunityCategory",
    "Percentage",
    "PersonalityTrait",
    "Priority",
    "PriorityQuadrant",
    "PricingPosture",
    "PricingSignalKind",
    "ProvenanceKind",
    "QualityBand",
    "ReachScore",
    "RetentionLeverKind",
    "RiskCategory",
    "RiskLevel",
    "Severity",
    "SocialProofKind",
    "StrategyRelation",
    "StrategyScore",
    "StrategyTier",
    "Tag",
    "TrustElementKind",
    "UrgencyKind",
]


class InvalidStrategyValueError(DesignDirectorError):
    """Raised when a strategy value object is constructed with invalid data."""

    code = "invalid_strategy_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance & structure                                                       #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The four upstream engines today; future insight sources (analytics, interviews,
    surveys, support, reviews, CRM, heatmaps) extend this additively.
    """

    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    REASONING = "reasoning"
    ANALYTICS = "analytics"
    INTERVIEW = "interview"
    SURVEY = "survey"
    SUPPORT = "support"
    REVIEW = "review"
    CRM = "crm"
    HEATMAP = "heatmap"


class StrategyTier(str, Enum):
    """The positioning tier a strategy commits to."""

    LUXURY = "luxury"
    PREMIUM = "premium"
    AFFORDABLE = "affordable"
    ENTERPRISE = "enterprise"
    TECHNICAL = "technical"
    MINIMAL = "minimal"


class DecisionType(str, Enum):
    """The strategic domain a decision belongs to."""

    GOAL = "goal"
    CUSTOMER = "customer"
    POSITIONING = "positioning"
    VALUE = "value"
    MESSAGING = "messaging"
    TRUST = "trust"
    PRICING = "pricing"
    OFFER = "offer"
    URGENCY = "urgency"
    SOCIAL_PROOF = "social_proof"
    RETENTION = "retention"


class DecisionRelation(str, Enum):
    """A typed, directed edge between two strategic decisions.

    ``DERIVES_FROM`` must be acyclic (a decision cannot ultimately derive from
    itself). ``CONFLICTS_WITH`` may be mutual — it surfaces a strategic tension to be
    resolved, not an error.
    """

    DERIVES_FROM = "derives_from"
    SUPPORTS = "supports"
    ENABLES = "enables"
    CONSTRAINS = "constrains"
    CONFLICTS_WITH = "conflicts_with"
    TRADES_OFF_AGAINST = "trades_off_against"


class StrategyRelation(str, Enum):
    """A typed edge between two strategy components (pillars)."""

    INFORMS = "informs"
    REINFORCES = "reinforces"
    DEPENDS_ON = "depends_on"
    TENSIONS_WITH = "tensions_with"


# --------------------------------------------------------------------------- #
# Customer psychology & journey                                                #
# --------------------------------------------------------------------------- #
class JourneyPhase(str, Enum):
    """A phase in the customer journey."""

    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    DECISION = "decision"
    PURCHASE = "purchase"
    RETENTION = "retention"
    ADVOCACY = "advocacy"


class JobType(str, Enum):
    """The category of a job-to-be-done (Christensen)."""

    FUNCTIONAL = "functional"
    EMOTIONAL = "emotional"
    SOCIAL = "social"


class EmotionKind(str, Enum):
    """An emotion a strategy intends to trigger, and thereby design for."""

    TRUST = "trust"
    DESIRE = "desire"
    CONFIDENCE = "confidence"
    BELONGING = "belonging"
    EXCLUSIVITY = "exclusivity"
    URGENCY = "urgency"
    RELIEF = "relief"
    DELIGHT = "delight"
    REASSURANCE = "reassurance"
    ASPIRATION = "aspiration"


class GoalCategory(str, Enum):
    """The category of a business goal."""

    REVENUE = "revenue"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ACQUISITION = "acquisition"
    AOV = "aov"
    BRAND = "brand"
    MARGIN = "margin"
    EXPANSION = "expansion"


class GoalHorizon(str, Enum):
    """The time horizon of a business goal."""

    SHORT_TERM = "short_term"
    MID_TERM = "mid_term"
    LONG_TERM = "long_term"


# --------------------------------------------------------------------------- #
# Messaging & brand                                                            #
# --------------------------------------------------------------------------- #
class MessagingTone(str, Enum):
    """The tone a brand's voice adopts."""

    AUTHORITATIVE = "authoritative"
    WARM = "warm"
    PLAYFUL = "playful"
    MINIMAL = "minimal"
    LUXURIOUS = "luxurious"
    TECHNICAL = "technical"
    REASSURING = "reassuring"
    BOLD = "bold"


class PersonalityTrait(str, Enum):
    """A brand personality trait (aligned to Aaker's brand dimensions)."""

    SINCERITY = "sincerity"
    EXCITEMENT = "excitement"
    COMPETENCE = "competence"
    SOPHISTICATION = "sophistication"
    RUGGEDNESS = "ruggedness"


# --------------------------------------------------------------------------- #
# Trust, pricing, retention                                                    #
# --------------------------------------------------------------------------- #
class TrustElementKind(str, Enum):
    """A kind of trust element a strategy requires the experience to carry."""

    REVIEWS = "reviews"
    RATINGS = "ratings"
    TESTIMONIALS = "testimonials"
    GUARANTEE = "guarantee"
    RETURN_POLICY = "return_policy"
    SECURE_CHECKOUT = "secure_checkout"
    CERTIFICATIONS = "certifications"
    PRESS_MENTIONS = "press_mentions"
    USER_GENERATED_CONTENT = "user_generated_content"
    TRANSPARENCY = "transparency"
    EXPERT_ENDORSEMENT = "expert_endorsement"


class SocialProofKind(str, Enum):
    """A kind of social proof."""

    CUSTOMER_REVIEWS = "customer_reviews"
    RATINGS_SUMMARY = "ratings_summary"
    USAGE_STATS = "usage_stats"
    INFLUENCER = "influencer"
    MEDIA_LOGOS = "media_logos"
    BESTSELLER_BADGES = "bestseller_badges"
    REAL_TIME_ACTIVITY = "real_time_activity"


class PricingPosture(str, Enum):
    """The overall pricing posture a strategy adopts."""

    PREMIUM = "premium"
    VALUE = "value"
    COMPETITIVE = "competitive"
    PENETRATION = "penetration"
    ANCHORED = "anchored"


class PricingSignalKind(str, Enum):
    """A pricing signal the experience should communicate."""

    ANCHOR_PRICE = "anchor_price"
    BUNDLE_VALUE = "bundle_value"
    INSTALLMENTS = "installments"
    FREE_SHIPPING_THRESHOLD = "free_shipping_threshold"
    PRICE_MATCH = "price_match"
    TIERED_PRICING = "tiered_pricing"
    SUBSCRIPTION_SAVINGS = "subscription_savings"


class UrgencyKind(str, Enum):
    """A kind of urgency — each must be honestly justified by evidence."""

    LOW_STOCK = "low_stock"
    TIME_LIMITED_OFFER = "time_limited_offer"
    SEASONAL = "seasonal"
    HIGH_DEMAND = "high_demand"
    EXCLUSIVE_DROP = "exclusive_drop"


class RetentionLeverKind(str, Enum):
    """A lever a retention strategy pulls."""

    LOYALTY_PROGRAM = "loyalty_program"
    SUBSCRIPTION = "subscription"
    POST_PURCHASE_NURTURE = "post_purchase_nurture"
    REPLENISHMENT = "replenishment"
    COMMUNITY = "community"
    PERSONALIZATION = "personalization"
    REFERRAL = "referral"


# --------------------------------------------------------------------------- #
# Risk & opportunity                                                           #
# --------------------------------------------------------------------------- #
class RiskCategory(str, Enum):
    """The category of a business risk."""

    MARKET = "market"
    COMPETITIVE = "competitive"
    CONVERSION = "conversion"
    TRUST = "trust"
    PRICING = "pricing"
    BRAND = "brand"
    OPERATIONAL = "operational"
    EVIDENCE_GAP = "evidence_gap"


class RiskLevel(str, Enum):
    """The severity band of a risk (from severity × likelihood)."""

    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class OpportunityCategory(str, Enum):
    """The category of a business or revenue opportunity."""

    CONVERSION = "conversion"
    AOV = "aov"
    RETENTION = "retention"
    ACQUISITION = "acquisition"
    TRUST = "trust"
    POSITIONING = "positioning"
    MERCHANDISING = "merchandising"


class PriorityQuadrant(str, Enum):
    """The impact/effort quadrant an initiative falls into."""

    QUICK_WIN = "quick_win"
    MAJOR_PROJECT = "major_project"
    FILL_IN = "fill_in"
    THANKLESS = "thankless"


class QualityBand(str, Enum):
    """A categorical band shared by the quality/score scales."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


# --------------------------------------------------------------------------- #
# Calibrated scales                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """A confidence value in ``[0, 1]``."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidStrategyValueError(
                "Confidence.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(1.0, max(0.0, value)))


@dataclass(frozen=True, slots=True, order=True)
class Percentage:
    """A fraction in ``[0, 1]`` (e.g. a coverage or grounding ratio)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidStrategyValueError(
                "Percentage.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def ratio(cls, present: int, total: int) -> Self:
        """The fraction ``present / total`` (1.0 when nothing is expected)."""
        if total <= 0:
            return cls(value=1.0)
        return cls(value=min(1.0, max(0.0, present / total)))


@dataclass(frozen=True, slots=True, order=True)
class StrategyScore:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidStrategyValueError(
                "StrategyScore.value must be within [0, 100].", details={"value": self.value}
            )

    @property
    def band(self) -> QualityBand:
        if self.value >= 80.0:
            return QualityBand.EXCELLENT
        if self.value >= 60.0:
            return QualityBand.GOOD
        if self.value >= 40.0:
            return QualityBand.FAIR
        return QualityBand.POOR

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(100.0, max(0.0, value)))


def _bounded_int(name: str, value: int, low: int, high: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidStrategyValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidStrategyValueError(
            f"{name} must be within [{low}, {high}].", details={"value": value}
        )
    return value


@dataclass(frozen=True, slots=True, order=True)
class Priority:
    """A 1–5 priority (5 = highest)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Priority", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Severity:
    """A 1–5 severity (5 = most severe)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Severity", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Likelihood:
    """A 1–5 likelihood (5 = most likely)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Likelihood", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ImpactScore:
    """A 1–5 impact estimate used in prioritization (5 = highest impact)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("ImpactScore", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class EffortScore:
    """A 1–5 effort estimate used in prioritization (5 = highest effort)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("EffortScore", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReachScore:
    """A 1–5 reach estimate used in RICE prioritization (5 = widest reach)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("ReachScore", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


_CURRENCY = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """A non-negative monetary amount in a 3-letter ISO currency.

    Ordered by amount then currency so revenue opportunities sort naturally.
    """

    amount: float
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidStrategyValueError(
                "Money.amount must be non-negative.", details={"amount": self.amount}
            )
        normalized = self.currency.strip().upper()
        if not _CURRENCY.match(normalized):
            raise InvalidStrategyValueError(
                "Money.currency must be a 3-letter ISO code.",
                details={"currency": self.currency},
            )
        object.__setattr__(self, "currency", normalized)

    @classmethod
    def of(cls, amount: float, currency: str = "USD") -> Self:
        return cls(amount=amount, currency=currency)


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A runner-up option a decision weighed and rejected — the trade-off record.

    A senior strategist does not just state a choice; they show what else was on the
    table and why it lost. Recording the considered alternative keeps every decision
    honest and auditable.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidStrategyValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidStrategyValueError(
                "ConsideredAlternative.reason_rejected must be non-empty."
            )


_TAG_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Tag:
    """A normalized free-form label (lower case, whitespace collapsed to hyphens)."""

    value: str

    def __post_init__(self) -> None:
        normalized = _TAG_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidStrategyValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
