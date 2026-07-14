"""Shared value objects for the Brand Strategy Engine.

These immutable, self-validating value objects are the vocabulary the engine reasons
in: the provenance of the evidence it cites, the archetypes and decision types it works
with, the voice dimensions and creative languages it chooses, the enforcement levels of
its governance, and the calibrated scales it scores everything on.

Everything here is pure domain: only the standard library and the shared-kernel error
base (:mod:`core.errors`). No framework, no I/O, no global mutable state, and no import
of any provider or other engine — those are reached only through ports, keeping this
domain independent.

Testing considerations
----------------------
* :class:`BrandCategory` has exactly thirteen members and :class:`BrandArchetype`
  exactly twelve.
* :class:`Confidence`, :class:`BrandScore`, :class:`Percentage`, :class:`Priority`, and
  :class:`Salience` validate their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "BrandArchetype",
    "BrandCategory",
    "BrandDecisionType",
    "BrandScore",
    "ColorTemperament",
    "ComponentWeight",
    "Confidence",
    "ConsideredAlternative",
    "ConsistencyDimension",
    "ContrastLevel",
    "CornerLanguage",
    "DecisionRelation",
    "EmotionKind",
    "GovernanceScope",
    "IconStyle",
    "IllustrationStyle",
    "InvalidBrandValueError",
    "MessagingTone",
    "MotionCharacter",
    "Percentage",
    "PhotoTreatment",
    "Priority",
    "ProvenanceKind",
    "QualityBand",
    "RuleEnforcement",
    "Salience",
    "SpacingDensity",
    "Tag",
    "TrustSignalKind",
    "TypeVoice",
    "UITexture",
    "ValidationSeverity",
    "VoiceDimension",
]


class InvalidBrandValueError(DesignDirectorError):
    """Raised when a brand value object is constructed with invalid data."""

    code = "invalid_brand_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance & structure                                                       #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The Business Strategy engine and the four platform engines today; future brand
    sources (audits, sentiment, trends, assets) extend this additively.
    """

    BUSINESS_STRATEGY = "business_strategy"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    REASONING = "reasoning"
    AUDIT = "audit"
    SENTIMENT = "sentiment"
    TREND = "trend"
    ASSET = "asset"


class BrandCategory(str, Enum):
    """The thirteen brand categories the engine classifies into.

    A blend of style register, market posture, and industry vertical — a brand may be
    tagged with a primary and several secondary categories.
    """

    LUXURY = "luxury"
    PREMIUM = "premium"
    MINIMAL = "minimal"
    TECHNICAL = "technical"
    LIFESTYLE = "lifestyle"
    MASS_MARKET = "mass_market"
    FASHION = "fashion"
    BEAUTY = "beauty"
    HEALTHCARE = "healthcare"
    SUPPLEMENTS = "supplements"
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    ENTERPRISE = "enterprise"


class BrandArchetype(str, Enum):
    """The twelve Jungian brand archetypes."""

    SAGE = "sage"
    HERO = "hero"
    CREATOR = "creator"
    RULER = "ruler"
    INNOCENT = "innocent"
    EXPLORER = "explorer"
    MAGICIAN = "magician"
    EVERYPERSON = "everyperson"
    LOVER = "lover"
    JESTER = "jester"
    CAREGIVER = "caregiver"
    OUTLAW = "outlaw"


class BrandDecisionType(str, Enum):
    """The brand domain a decision belongs to."""

    POSITIONING = "positioning"
    MISSION = "mission"
    VISION = "vision"
    VALUES = "values"
    PROMISE = "promise"
    STORY = "story"
    ARCHETYPE = "archetype"
    PERSONALITY = "personality"
    ATTRIBUTES = "attributes"
    VOICE = "voice"
    EMOTIONAL = "emotional"
    TRUST = "trust"
    DIFFERENTIATION = "differentiation"
    LOGO = "logo"
    TYPOGRAPHY = "typography"
    COLOR = "color"
    SPACING = "spacing"
    PHOTOGRAPHY = "photography"
    ILLUSTRATION = "illustration"
    ICONOGRAPHY = "iconography"
    MOTION = "motion"
    UI_PERSONALITY = "ui_personality"
    COMPONENT_PERSONALITY = "component_personality"
    LANGUAGE = "language"
    COPY = "copy"


class DecisionRelation(str, Enum):
    """A typed, directed edge between two brand decisions.

    ``DERIVES_FROM`` must be acyclic. ``EXPRESSES`` links a creative decision to the
    identity trait it gives form to. ``CONFLICTS_WITH`` may be mutual — a tension to
    resolve, not an error.
    """

    DERIVES_FROM = "derives_from"
    EXPRESSES = "expresses"
    SUPPORTS = "supports"
    ENABLES = "enables"
    CONSTRAINS = "constrains"
    CONFLICTS_WITH = "conflicts_with"


# --------------------------------------------------------------------------- #
# Verbal & emotional                                                           #
# --------------------------------------------------------------------------- #
class VoiceDimension(str, Enum):
    """The four dimensions of tone of voice (Nielsen Norman).

    Each is a spectrum; a :class:`~brand.domain.personality.voice.BrandVoice` places
    the brand on each via a :class:`Percentage` (0 = first pole, 1 = second pole).
    """

    FORMALITY = "formality"  # 0 casual → 1 formal
    HUMOR = "humor"  # 0 serious → 1 funny
    RESPECT = "respect"  # 0 irreverent → 1 respectful
    ENTHUSIASM = "enthusiasm"  # 0 matter_of_fact → 1 enthusiastic


class MessagingTone(str, Enum):
    """The dominant tone a brand's voice adopts."""

    AUTHORITATIVE = "authoritative"
    WARM = "warm"
    PLAYFUL = "playful"
    MINIMAL = "minimal"
    LUXURIOUS = "luxurious"
    TECHNICAL = "technical"
    REASSURING = "reassuring"
    BOLD = "bold"
    ELEGANT = "elegant"


class EmotionKind(str, Enum):
    """An emotion a brand intends to evoke."""

    TRUST = "trust"
    DESIRE = "desire"
    CONFIDENCE = "confidence"
    BELONGING = "belonging"
    EXCLUSIVITY = "exclusivity"
    DELIGHT = "delight"
    REASSURANCE = "reassurance"
    ASPIRATION = "aspiration"
    CALM = "calm"
    EMPOWERMENT = "empowerment"


class TrustSignalKind(str, Enum):
    """A kind of brand trust signal."""

    REVIEWS = "reviews"
    RATINGS = "ratings"
    GUARANTEE = "guarantee"
    CERTIFICATIONS = "certifications"
    PRESS = "press"
    TRANSPARENCY = "transparency"
    HERITAGE = "heritage"
    EXPERT_ENDORSEMENT = "expert_endorsement"
    SECURITY = "security"
    SOCIAL_PROOF = "social_proof"


# --------------------------------------------------------------------------- #
# Creative languages (strategic intent, never tokens)                          #
# --------------------------------------------------------------------------- #
class ColorTemperament(str, Enum):
    """The overall temperature of a colour philosophy."""

    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ContrastLevel(str, Enum):
    """The contrast register a brand's visual system expresses."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DRAMATIC = "dramatic"


class TypeVoice(str, Enum):
    """The character of a typographic voice."""

    EDITORIAL_SERIF = "editorial_serif"
    TRANSITIONAL_SERIF = "transitional_serif"
    HUMANIST_SANS = "humanist_sans"
    GEOMETRIC_SANS = "geometric_sans"
    GROTESQUE_SANS = "grotesque_sans"
    MONOSPACE = "monospace"
    DISPLAY = "display"


class SpacingDensity(str, Enum):
    """The spatial density a brand's layout philosophy calls for."""

    AIRY = "airy"
    BALANCED = "balanced"
    COMPACT = "compact"
    DENSE = "dense"


class PhotoTreatment(str, Enum):
    """The treatment of brand photography."""

    EDITORIAL = "editorial"
    LIFESTYLE = "lifestyle"
    STUDIO = "studio"
    DOCUMENTARY = "documentary"
    MINIMAL = "minimal"
    BOLD = "bold"


class IllustrationStyle(str, Enum):
    """The style of brand illustration (``NONE`` when illustration is not used)."""

    NONE = "none"
    LINE = "line"
    FLAT = "flat"
    ORGANIC = "organic"
    GEOMETRIC = "geometric"
    EDITORIAL = "editorial"


class IconStyle(str, Enum):
    """The style of brand iconography."""

    LINE = "line"
    SOLID = "solid"
    DUOTONE = "duotone"
    ROUNDED = "rounded"
    SHARP = "sharp"


class MotionCharacter(str, Enum):
    """The character of brand motion."""

    SUBTLE = "subtle"
    FLUID = "fluid"
    PRECISE = "precise"
    PLAYFUL = "playful"
    DRAMATIC = "dramatic"
    MINIMAL = "minimal"


class CornerLanguage(str, Enum):
    """The corner treatment that expresses a UI's personality."""

    SHARP = "sharp"
    SLIGHTLY_ROUNDED = "slightly_rounded"
    ROUNDED = "rounded"
    PILL = "pill"


class ComponentWeight(str, Enum):
    """The visual weight a component personality carries."""

    LIGHT = "light"
    REGULAR = "regular"
    MEDIUM = "medium"
    BOLD = "bold"


class UITexture(str, Enum):
    """The texture/depth a UI personality expresses."""

    FLAT = "flat"
    SUBTLE_DEPTH = "subtle_depth"
    LAYERED = "layered"
    TACTILE = "tactile"


# --------------------------------------------------------------------------- #
# Governance                                                                   #
# --------------------------------------------------------------------------- #
class GovernanceScope(str, Enum):
    """The scope a governance rule applies to."""

    IDENTITY = "identity"
    VISUAL = "visual"
    VERBAL = "verbal"
    EXPERIENCE = "experience"
    ALL = "all"


class ConsistencyDimension(str, Enum):
    """The dimension a consistency rule guards."""

    VOICE = "voice"
    TONE = "tone"
    TERMINOLOGY = "terminology"
    COLOR = "color"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    MOTION = "motion"
    IMAGERY = "imagery"
    TRUST = "trust"


class ValidationSeverity(str, Enum):
    """The severity of a validation rule breach."""

    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class RuleEnforcement(str, Enum):
    """The enforcement strength of a rule (RFC-2119 register)."""

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
            raise InvalidBrandValueError(
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
    """A fraction in ``[0, 1]`` (e.g. a coverage ratio or a voice-spectrum position)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidBrandValueError(
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
class BrandScore:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidBrandValueError(
                "BrandScore.value must be within [0, 100].", details={"value": self.value}
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
        raise InvalidBrandValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidBrandValueError(
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
class Salience:
    """A 1–5 salience/prominence (5 = most prominent)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Salience", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A runner-up option a decision weighed and rejected — the trade-off record.

    A world-class brand strategist does not just state a choice; they show what else was
    on the table and why it lost. Recording the considered alternative keeps every
    decision honest and auditable.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidBrandValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidBrandValueError(
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
            raise InvalidBrandValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
