"""Shared value objects for the UX Strategy Engine.

These immutable, self-validating value objects are the vocabulary the engine reasons in:
the provenance of the evidence it cites, the pages and journeys it defines, the UX laws
and heuristics it applies, the kinds of graph it builds, and the calibrated scales it
scores everything on.

Everything here is pure domain: only the standard library and the shared-kernel error
base (:mod:`core.errors`). No framework, no I/O, no global mutable state, and no import of
any provider or other engine — those are reached only through ports, keeping this domain
independent.

Testing considerations
----------------------
* :class:`UXLaw` has exactly eleven members (the required laws/heuristics),
  :class:`PageKind` nine, and :class:`JourneyKind` seven.
* :class:`Confidence`, :class:`UXScore`, :class:`Percentage`, :class:`Priority`,
  :class:`Severity`, :class:`Effort`, and :class:`Impact` validate their ranges and order
  by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "CTAType",
    "Confidence",
    "ConsideredAlternative",
    "ContentType",
    "DeviceContext",
    "DropoffKind",
    "Effort",
    "FrictionKind",
    "GraphKind",
    "GraphRelation",
    "Impact",
    "InformationLevel",
    "InteractionPattern",
    "InvalidUXValueError",
    "JourneyKind",
    "JourneyPhase",
    "MetricKind",
    "NavPattern",
    "NodeKind",
    "PageKind",
    "Percentage",
    "Priority",
    "ProvenanceKind",
    "QualityBand",
    "RuleEnforcement",
    "Severity",
    "Tag",
    "UXLaw",
    "UXScore",
    "WCAGLevel",
]


class InvalidUXValueError(DesignDirectorError):
    """Raised when a UX value object is constructed with invalid data."""

    code = "invalid_ux_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The upstream strategy/psychology engines and the platform engines today; future
    behavioral-analytics sources (heatmaps, GA4, PostHog, …) extend this additively.
    """

    PSYCHOLOGY = "psychology"
    BRAND_STRATEGY = "brand_strategy"
    BUSINESS_STRATEGY = "business_strategy"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    REASONING = "reasoning"
    ANALYTICS = "analytics"
    HEATMAP = "heatmap"
    SESSION_REPLAY = "session_replay"
    AB_TEST = "ab_test"
    GA4 = "ga4"
    POSTHOG = "posthog"
    CLARITY = "clarity"


# --------------------------------------------------------------------------- #
# Pages, journeys, flows                                                       #
# --------------------------------------------------------------------------- #
class PageKind(str, Enum):
    """A key page/surface the UX strategy defines."""

    HOME = "home"
    CATEGORY = "category"
    PRODUCT = "product"
    SEARCH = "search"
    CART = "cart"
    CHECKOUT = "checkout"
    ACCOUNT = "account"
    POST_PURCHASE = "post_purchase"
    LANDING = "landing"


class JourneyKind(str, Enum):
    """One of the seven UX journeys."""

    USER = "user"
    TASK = "task"
    DECISION = "decision"
    TRUST = "trust"
    CONVERSION = "conversion"
    MOBILE = "mobile"
    ACCESSIBILITY = "accessibility"


class FlowKind(str, Enum):
    """The kind of flow."""

    USER = "user"
    TASK = "task"


class JourneyPhase(str, Enum):
    """A phase in the customer journey (aligned with the psychology engine)."""

    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    DECISION = "decision"
    PURCHASE = "purchase"
    POST_PURCHASE = "post_purchase"
    ADVOCACY = "advocacy"


class CTAType(str, Enum):
    """The prominence tier of a call to action."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class DeviceContext(str, Enum):
    """The device context a journey or page is optimised for."""

    MOBILE = "mobile"
    DESKTOP = "desktop"
    RESPONSIVE = "responsive"


# --------------------------------------------------------------------------- #
# Content, navigation, interaction                                             #
# --------------------------------------------------------------------------- #
class InformationLevel(str, Enum):
    """The disclosure level of a piece of information (progressive disclosure)."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    HIDDEN = "hidden"


class ContentType(str, Enum):
    """A kind of content the strategy prioritises."""

    VALUE_PROPOSITION = "value_proposition"
    PRODUCT_INFO = "product_info"
    SOCIAL_PROOF = "social_proof"
    TRUST_SIGNAL = "trust_signal"
    PRICING = "pricing"
    CTA = "cta"
    NAVIGATION = "navigation"
    SUPPORT = "support"
    POLICY = "policy"


class NavPattern(str, Enum):
    """The overall navigation pattern."""

    FLAT = "flat"
    HUB_AND_SPOKE = "hub_and_spoke"
    HIERARCHICAL = "hierarchical"
    FACETED = "faceted"
    MIXED = "mixed"


class InteractionPattern(str, Enum):
    """An interaction pattern the strategy calls for."""

    INLINE_VALIDATION = "inline_validation"
    OPTIMISTIC_FEEDBACK = "optimistic_feedback"
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"
    STICKY_ACTION = "sticky_action"
    GUIDED_STEPS = "guided_steps"
    UNDO = "undo"
    AUTOSAVE = "autosave"


class WCAGLevel(str, Enum):
    """A WCAG conformance level."""

    A = "a"
    AA = "aa"
    AAA = "aaa"


# --------------------------------------------------------------------------- #
# Analysis                                                                     #
# --------------------------------------------------------------------------- #
class FrictionKind(str, Enum):
    """A kind of experience friction."""

    COGNITIVE = "cognitive"
    NAVIGATION = "navigation"
    FORM = "form"
    TRUST = "trust"
    PERFORMANCE = "performance"
    CONTENT = "content"
    DECISION = "decision"
    ACCESSIBILITY = "accessibility"


class DropoffKind(str, Enum):
    """A kind of drop-off risk."""

    ANXIETY = "anxiety"
    DISTRACTION = "distraction"
    COMPLEXITY = "complexity"
    COST_SHOCK = "cost_shock"
    TRUST_GAP = "trust_gap"
    DEAD_END = "dead_end"
    SLOW_LOAD = "slow_load"


class MetricKind(str, Enum):
    """A kind of success metric a page is measured by."""

    CONVERSION_RATE = "conversion_rate"
    ADD_TO_CART_RATE = "add_to_cart_rate"
    CHECKOUT_COMPLETION = "checkout_completion"
    BOUNCE_RATE = "bounce_rate"
    TIME_ON_TASK = "time_on_task"
    ENGAGEMENT = "engagement"
    RETURN_RATE = "return_rate"
    AOV = "aov"


# --------------------------------------------------------------------------- #
# UX laws                                                                      #
# --------------------------------------------------------------------------- #
class UXLaw(str, Enum):
    """A UX law / heuristic the engine applies."""

    JAKOBS = "jakobs_law"
    HICKS = "hicks_law"
    FITTS = "fitts_law"
    MILLERS = "millers_law"
    TESLERS = "teslers_law"
    OCCAMS = "occams_razor"
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"
    GESTALT = "gestalt_principles"
    NIELSEN_HEURISTICS = "nielsen_heuristics"
    BAYMARD = "baymard_ux"
    WCAG = "wcag"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the five UX graphs."""

    DECISION = "decision"
    NAVIGATION = "navigation"
    CONTENT_HIERARCHY = "content_hierarchy"
    TRUST_HIERARCHY = "trust_hierarchy"
    INTERACTION = "interaction"


class NodeKind(str, Enum):
    """The kind of node a UX-graph node represents."""

    PAGE = "page"
    DECISION = "decision"
    CONTENT = "content"
    TRUST_ELEMENT = "trust_element"
    INTERACTION = "interaction"
    CTA = "cta"
    STEP = "step"
    NAV_ITEM = "nav_item"


class GraphRelation(str, Enum):
    """A typed, directed edge between two UX-graph nodes.

    ``LEADS_TO``, ``PRECEDES``, ``DERIVES_FROM`` and ``CONTAINS`` must be acyclic.
    ``CONFLICTS_WITH`` may be mutual — a tension to resolve, not an error.
    """

    LEADS_TO = "leads_to"
    LINKS_TO = "links_to"
    CONTAINS = "contains"
    PRECEDES = "precedes"
    DERIVES_FROM = "derives_from"
    BLOCKS = "blocks"
    SUPPORTS = "supports"
    CONFLICTS_WITH = "conflicts_with"


class RuleEnforcement(str, Enum):
    """The enforcement strength of a UX guideline (RFC-2119 register)."""

    MUST = "must"
    SHOULD = "should"
    MAY = "may"


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
            raise InvalidUXValueError(
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
            raise InvalidUXValueError(
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
class UXScore:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidUXValueError(
                "UXScore.value must be within [0, 100].", details={"value": self.value}
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
        raise InvalidUXValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidUXValueError(
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
class Effort:
    """A 1–5 effort estimate (5 = highest effort)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Effort", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Impact:
    """A 1–5 impact estimate (5 = highest impact)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Impact", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A runner-up option the engine weighed and rejected — the trade-off record.

    A principal UX strategist does not just state a decision; they show what else fit the
    evidence and why it lost. Recording the considered alternative keeps every decision
    honest and auditable.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidUXValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidUXValueError(
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
            raise InvalidUXValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
