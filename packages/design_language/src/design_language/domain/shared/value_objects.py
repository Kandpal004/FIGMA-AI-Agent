"""Shared value objects for the Design Language Engine.

These immutable, self-validating value objects are the vocabulary the engine designs in: the
provenance of the evidence it cites, the supported language archetypes and industry presets,
the visual-style and leveled attributes it determines, the philosophy and personality kinds it
elaborates, the token/color/responsive strategies it defines, the rule and constraint kinds it
enforces, the kinds of graph it builds, and the calibrated scales it reasons on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, and no import of any provider or other engine —
those are reached only through ports. This engine defines a visual *language*, never pixels:
nothing here is a hex colour, a font name, or a rendered value — only the abstract character
those must express.

Testing considerations
----------------------
* :class:`LanguageArchetype` has the nineteen supported languages (plus a custom blend),
  :class:`IndustryPreset` the twelve industries, :class:`GraphKind` exactly two.
* :class:`Confidence`, :class:`Score`, :class:`Percentage`, :class:`Level`, and :class:`Ratio`
  validate their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AlignmentApproach",
    "ColorRole",
    "ColorStrategy",
    "Confidence",
    "ConsideredAlternative",
    "ConsistencyKind",
    "CompositionKind",
    "ConstraintKind",
    "ContrastLevel",
    "Density",
    "GraphKind",
    "GraphRelation",
    "IndustryPreset",
    "InvalidDLValueError",
    "LanguageArchetype",
    "Level",
    "NodeKind",
    "PersonalityKind",
    "PhilosophyKind",
    "Percentage",
    "Ratio",
    "Rank",
    "ResponsiveApproach",
    "Rhythm",
    "Score",
    "QualityBand",
    "ProvenanceKind",
    "Tag",
    "VisualStyle",
    "VisualWeight",
]


class InvalidDLValueError(DesignDirectorError):
    """Raised when a Design Language value object is constructed with invalid data."""

    code = "invalid_design_language_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates — the seven upstream engines."""

    BUSINESS_STRATEGY = "business_strategy"
    BRAND_STRATEGY = "brand_strategy"
    PSYCHOLOGY = "psychology"
    CREATIVE_DIRECTOR = "creative_director"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    FIGMA = "figma"
    ANALYTICS = "analytics"


# --------------------------------------------------------------------------- #
# Languages & industries                                                       #
# --------------------------------------------------------------------------- #
class LanguageArchetype(str, Enum):
    """One of the nineteen supported design languages (plus a synthesised blend)."""

    APPLE = "apple"
    SHOPIFY_POLARIS = "shopify_polaris"
    MATERIAL_3 = "material_3"
    ATLASSIAN = "atlassian"
    LINEAR = "linear"
    STRIPE = "stripe"
    NOTION = "notion"
    NIKE = "nike"
    GYMSHARK = "gymshark"
    AESOP = "aesop"
    DYSON = "dyson"
    NOTHING = "nothing"
    LUXURY_FASHION = "luxury_fashion"
    LUXURY_BEAUTY = "luxury_beauty"
    PREMIUM_ELECTRONICS = "premium_electronics"
    PREMIUM_SUPPLEMENTS = "premium_supplements"
    ENTERPRISE_SAAS = "enterprise_saas"
    MINIMAL_EDITORIAL = "minimal_editorial"
    CUSTOM_BLEND = "custom_blend"


class IndustryPreset(str, Enum):
    """One of the twelve supported industry presets."""

    FASHION = "fashion"
    BEAUTY = "beauty"
    LUXURY = "luxury"
    JEWELLERY = "jewellery"
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    SUPPLEMENTS = "supplements"
    HEALTHCARE = "healthcare"
    FOOD = "food"
    PET = "pet"
    B2B = "b2b"
    MARKETPLACE = "marketplace"


# --------------------------------------------------------------------------- #
# Visual DNA attributes                                                        #
# --------------------------------------------------------------------------- #
class VisualStyle(str, Enum):
    """The overall visual posture of the language."""

    MINIMAL = "minimal"
    EDITORIAL = "editorial"
    BOLD = "bold"
    ORGANIC = "organic"
    TECHNICAL = "technical"
    LUXE = "luxe"
    WARM = "warm"
    UTILITARIAN = "utilitarian"


class Density(str, Enum):
    """How tightly the language packs information."""

    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    SPACIOUS = "spacious"
    AIRY = "airy"


class VisualWeight(str, Enum):
    """The perceived heaviness of the language."""

    LIGHT = "light"
    BALANCED = "balanced"
    HEAVY = "heavy"


class ContrastLevel(str, Enum):
    """The contrast posture of the language."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DRAMATIC = "dramatic"


class Rhythm(str, Enum):
    """The spacing/pacing rhythm of the language."""

    TIGHT = "tight"
    MEASURED = "measured"
    RELAXED = "relaxed"


# --------------------------------------------------------------------------- #
# Philosophies & personalities                                                 #
# --------------------------------------------------------------------------- #
class PhilosophyKind(str, Enum):
    """The eleven philosophies the language elaborates."""

    SPACING = "spacing"
    GRID = "grid"
    ALIGNMENT = "alignment"
    CONTAINER = "container"
    ELEVATION = "elevation"
    SURFACE = "surface"
    MOTION = "motion"
    INTERACTION = "interaction"
    ANIMATION = "animation"
    LAYOUT = "layout"
    COMPONENT = "component"


class PersonalityKind(str, Enum):
    """The four visual personalities the language expresses."""

    TYPOGRAPHY = "typography"
    ICONOGRAPHY = "iconography"
    ILLUSTRATION = "illustration"
    PHOTOGRAPHY = "photography"


class AlignmentApproach(str, Enum):
    """A grid/type alignment posture (referenced by rules and the grid system)."""

    OPTICAL = "optical"
    BASELINE = "baseline"
    GRID_SNAPPED = "grid_snapped"
    CENTERED = "centered"


# --------------------------------------------------------------------------- #
# Tokens, colour, responsive                                                   #
# --------------------------------------------------------------------------- #
class ColorStrategy(str, Enum):
    """The colour posture (a strategy, never concrete hex)."""

    MONOCHROME = "monochrome"
    NEUTRAL_ACCENT = "neutral_accent"
    DUOTONE = "duotone"
    MUTED = "muted"
    VIBRANT = "vibrant"
    EARTHY = "earthy"
    HIGH_CONTRAST_BW = "high_contrast_bw"


class ColorRole(str, Enum):
    """An abstract colour role (its concrete value is the Design System's job)."""

    BACKGROUND = "background"
    SURFACE = "surface"
    PRIMARY_TEXT = "primary_text"
    SECONDARY_TEXT = "secondary_text"
    ACCENT = "accent"
    BORDER = "border"
    MUTED = "muted"


class ResponsiveApproach(str, Enum):
    """The responsive posture of the language."""

    FLUID = "fluid"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


# --------------------------------------------------------------------------- #
# Rules & constraints                                                          #
# --------------------------------------------------------------------------- #
class ConsistencyKind(str, Enum):
    """A dimension a consistency rule governs."""

    SPACING_RHYTHM = "spacing_rhythm"
    TYPE_SCALE = "type_scale"
    CONTRAST = "contrast"
    ELEVATION = "elevation"
    ALIGNMENT = "alignment"
    MOTION = "motion"
    COLOR_ROLE = "color_role"


class CompositionKind(str, Enum):
    """A dimension a composition rule governs."""

    GRID = "grid"
    HIERARCHY = "hierarchy"
    PROXIMITY = "proximity"
    BALANCE = "balance"
    WHITESPACE = "whitespace"
    FOCAL_POINT = "focal_point"


class ConstraintKind(str, Enum):
    """A hard visual boundary that guards restraint and timelessness."""

    ACCENT_LIMIT = "accent_limit"
    DECORATION_LIMIT = "decoration_limit"
    CONTRAST_FLOOR = "contrast_floor"
    SPACING_FLOOR = "spacing_floor"
    MOTION_CEILING = "motion_ceiling"
    TREND_AVOIDANCE = "trend_avoidance"
    GENERIC_PATTERN_BAN = "generic_pattern_ban"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the two design-language graphs."""

    VISUAL = "visual"
    LANGUAGE = "language"


class NodeKind(str, Enum):
    """The kind of node a design-language-graph node represents."""

    DNA = "dna"
    PHILOSOPHY = "philosophy"
    PERSONALITY = "personality"
    TOKEN = "token"
    SYSTEM = "system"
    CONSTRAINT = "constraint"
    ARCHETYPE = "archetype"
    ALTERNATIVE = "alternative"
    TRAIT = "trait"


class GraphRelation(str, Enum):
    """A typed, directed edge between two design-language-graph nodes.

    All relations are acyclic — a language derivation is a directed rationale, never a cycle.
    """

    EXPRESSES = "expresses"
    ELABORATES = "elaborates"
    MATERIALISES = "materialises"
    CONSTRAINS = "constrains"
    SELECTS = "selects"
    REJECTS = "rejects"
    INFLUENCES = "influences"
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
            raise InvalidDLValueError(
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
            raise InvalidDLValueError(
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
            raise InvalidDLValueError(
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
        raise InvalidDLValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidDLValueError(
            f"{name} must be within [{low}, {high}].", details={"value": value}
        )
    return value


@dataclass(frozen=True, slots=True, order=True)
class Level:
    """A 1–5 level (5 = highest) — used for luxury and minimalism."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Level", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Ratio:
    """A modular ratio greater than 1 (e.g. a type scale ratio like 1.25)."""

    value: float

    def __post_init__(self) -> None:
        if not self.value > 1.0:
            raise InvalidDLValueError(
                "Ratio.value must be greater than 1.", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)


@dataclass(frozen=True, slots=True, order=True)
class Rank:
    """A 1-based ordinal rank (1 = first)."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 1:
            raise InvalidDLValueError("Rank must be an int >= 1.", details={"value": self.value})

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A language the engine weighed and rejected — the trade-off record.

    An Apple- or Pentagram-calibre design director never states a language without showing
    what else fit and why it lost. Recording the considered alternative makes the selection a
    deliberate, defensible choice rather than a default.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidDLValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidDLValueError(
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
            raise InvalidDLValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
