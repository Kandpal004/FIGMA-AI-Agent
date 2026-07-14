"""Shared value objects for the Creative Director Engine.

These immutable, self-validating value objects are the vocabulary the engine rules in: the
provenance of the evidence it cites, the sixteen dimensions it reviews, the fifteen
categories it scores, the review profiles and modes it operates under, the anti-patterns it is
built to reject, the approval statuses it issues, the kinds of graph it builds, and the
calibrated scales it judges everything on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, no global mutable state, and no import of any
provider or other engine — those are reached only through ports, keeping this domain
independent. This engine is a deterministic review-and-approval system; nothing in this
vocabulary is an LLM prompt or a probabilistic knob — every value is a hard, auditable fact.

Testing considerations
----------------------
* :class:`ReviewDimension` has exactly sixteen members, :class:`ScoreCategory` exactly
  fifteen, :class:`GraphKind` exactly five.
* :class:`Confidence`, :class:`Score`, :class:`Weight`, :class:`Percentage`, and
  :class:`Priority` validate their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AntiPattern",
    "ApprovalStatus",
    "Confidence",
    "DeciderRole",
    "FindingSeverity",
    "GraphKind",
    "GraphRelation",
    "InvalidCDValueError",
    "NodeKind",
    "Percentage",
    "Priority",
    "ProvenanceKind",
    "QualityBand",
    "ReviewDimension",
    "ReviewMode",
    "ReviewProfileKind",
    "ScoreCategory",
    "Score",
    "SubjectKind",
    "Tag",
    "Verdict",
    "Weight",
]


class InvalidCDValueError(DesignDirectorError):
    """Raised when a Creative Director value object is constructed with invalid data."""

    code = "invalid_creative_director_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance & subject                                                         #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The ten upstream engines the Creative Director reviews against, plus a human reviewer's
    input and a reserved future Figma source.
    """

    BUSINESS_STRATEGY = "business_strategy"
    BRAND_STRATEGY = "brand_strategy"
    PSYCHOLOGY = "psychology"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    UX_STRATEGY = "ux_strategy"
    INFORMATION_ARCHITECTURE = "information_architecture"
    WIREFRAME = "wireframe"
    HUMAN_REVIEWER = "human_reviewer"
    FIGMA = "figma"


class SubjectKind(str, Enum):
    """What is under review."""

    WIREFRAME_PLAN = "wireframe_plan"
    INFORMATION_ARCHITECTURE = "information_architecture"
    UX_STRATEGY = "ux_strategy"
    FIGMA = "figma"


# --------------------------------------------------------------------------- #
# Review dimensions & score categories                                         #
# --------------------------------------------------------------------------- #
class ReviewDimension(str, Enum):
    """One of the sixteen dimensions the Creative Director reviews."""

    BUSINESS_ALIGNMENT = "business_alignment"
    BRAND_ALIGNMENT = "brand_alignment"
    PSYCHOLOGY_ALIGNMENT = "psychology_alignment"
    UX_QUALITY = "ux_quality"
    INFORMATION_HIERARCHY = "information_hierarchy"
    CONVERSION_STRATEGY = "conversion_strategy"
    TRUST_SIGNALS = "trust_signals"
    TYPOGRAPHY_DIRECTION = "typography_direction"
    SPACING_LOGIC = "spacing_logic"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE_IMPACT = "performance_impact"
    MOBILE_EXPERIENCE = "mobile_experience"
    DEVELOPER_FEASIBILITY = "developer_feasibility"
    SHOPIFY_COMPATIBILITY = "shopify_compatibility"
    MAGENTO_COMPATIBILITY = "magento_compatibility"
    FUTURE_SCALABILITY = "future_scalability"


class ScoreCategory(str, Enum):
    """One of the fifteen scoring categories (``OVERALL`` is the weighted roll-up)."""

    BUSINESS = "business"
    BRAND = "brand"
    UX = "ux"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    TRUST = "trust"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    VISUAL_HIERARCHY = "visual_hierarchy"
    CONSISTENCY = "consistency"
    SCALABILITY = "scalability"
    DEVELOPER_EXPERIENCE = "developer_experience"
    MAINTAINABILITY = "maintainability"
    CONVERSION = "conversion"
    OVERALL = "overall"


# --------------------------------------------------------------------------- #
# Findings, verdicts, anti-patterns                                            #
# --------------------------------------------------------------------------- #
class Verdict(str, Enum):
    """The pass/fail outcome of a dimension review or the whole review."""

    PASS = "pass"
    FAIL = "fail"


class FindingSeverity(str, Enum):
    """How much a finding matters to approval."""

    BLOCKING = "blocking"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"


class AntiPattern(str, Enum):
    """A design anti-pattern the Creative Director is built to detect and reject."""

    GENERIC_LAYOUT = "generic_layout"
    WEAK_TYPOGRAPHY = "weak_typography"
    POOR_SPACING = "poor_spacing"
    WEAK_HIERARCHY = "weak_hierarchy"
    POOR_CRO = "poor_cro"
    LOW_TRUST = "low_trust"
    GENERIC_AI_PATTERN = "generic_ai_pattern"
    DECORATIVE_WITHOUT_PURPOSE = "decorative_without_purpose"


# --------------------------------------------------------------------------- #
# Profiles, modes, approval, deciders                                          #
# --------------------------------------------------------------------------- #
class ReviewProfileKind(str, Enum):
    """A calibrated review profile — reweights categories and sets gates/thresholds."""

    STARTUP = "startup"
    ENTERPRISE = "enterprise"
    LUXURY = "luxury"
    MARKETPLACE = "marketplace"
    D2C = "d2c"
    B2B = "b2b"


class ReviewMode(str, Enum):
    """How the final approval decision is arrived at."""

    AUTOMATIC = "automatic"
    HUMAN_ASSISTED = "human_assisted"
    CREATIVE_DIRECTOR_OVERRIDE = "creative_director_override"
    REVIEW_COMMITTEE = "review_committee"


class ApprovalStatus(str, Enum):
    """The Creative Director's ruling on a subject."""

    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    ESCALATED = "escalated"


class DeciderRole(str, Enum):
    """Who issued a decision."""

    SYSTEM = "system"
    CREATIVE_DIRECTOR = "creative_director"
    COMMITTEE = "committee"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the five Creative Director graphs."""

    REVIEW = "review"
    DECISION = "decision"
    APPROVAL = "approval"
    QUALITY_MATRIX = "quality_matrix"
    IMPROVEMENT_MATRIX = "improvement_matrix"


class NodeKind(str, Enum):
    """The kind of node a review-graph node represents."""

    SUBJECT = "subject"
    DIMENSION = "dimension"
    FINDING = "finding"
    CHANGE = "change"
    CATEGORY = "category"
    DECISION = "decision"
    GATE = "gate"


class GraphRelation(str, Enum):
    """A typed, directed edge between two review-graph nodes.

    All relations are acyclic — a review is a directed audit, never a cycle.
    """

    REVIEWS = "reviews"
    RAISES = "raises"
    REQUIRES_FIX = "requires_fix"
    SCORES = "scores"
    INFORMS = "informs"
    GATES = "gates"
    SUPERSEDES = "supersedes"
    DERIVES_FROM = "derives_from"


class QualityBand(str, Enum):
    """A categorical band shared by the score scales."""

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
            raise InvalidCDValueError(
                "Confidence.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(1.0, max(0.0, value)))


@dataclass(frozen=True, slots=True, order=True)
class Weight:
    """A weight in ``[0, 1]`` (a category's share of the overall score)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidCDValueError(
                "Weight.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)


@dataclass(frozen=True, slots=True, order=True)
class Percentage:
    """A fraction in ``[0, 1]`` (e.g. a grounding or coverage ratio)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidCDValueError(
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
class Score:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidCDValueError(
                "Score.value must be within [0, 100].", details={"value": self.value}
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
        raise InvalidCDValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidCDValueError(
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


_TAG_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Tag:
    """A normalized free-form label (lower case, whitespace collapsed to hyphens)."""

    value: str

    def __post_init__(self) -> None:
        normalized = _TAG_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidCDValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
