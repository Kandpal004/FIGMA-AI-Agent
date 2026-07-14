"""Shared value objects for the Competitor Intelligence Engine.

These immutable, self-validating value objects are the vocabulary the engine
reasons in: how competitors are tiered, the dimensions they are profiled across,
where an observation came from, the kinds of pattern detected, and the calibrated
scales used to benchmark, weigh confidence, gauge prevalence, and rate risk.

Everything here is pure domain: only the standard library and the shared-kernel
error base (:mod:`core.errors`). No framework, no I/O, no global mutable state, and
crucially **no import of the Knowledge/Reasoning engines** — those are reached only
through ports, keeping this domain independent.

Testing considerations
----------------------
* :class:`Score` validates ``[0, 100]`` and orders by value.
* :class:`BenchmarkBand.from_relative` deterministically classifies a score
  against a category benchmark.
* :class:`Prevalence` validates ``0 <= count <= total`` and derives its band.
* :class:`Confidence` validates ``[0, 1]`` and derives its band.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "BenchmarkBand",
    "CompetitorDimension",
    "CompetitorTier",
    "Confidence",
    "ConfidenceBand",
    "InvalidCompetitiveValueError",
    "Likelihood",
    "ObservationSource",
    "PatternKind",
    "Prevalence",
    "PrevalenceBand",
    "RecommendationAction",
    "Score",
    "Severity",
]


class InvalidCompetitiveValueError(DesignDirectorError):
    """Raised when a competitive value object is constructed with invalid data."""

    code = "invalid_competitive_value"
    http_status = 422


class CompetitorTier(str, Enum):
    """How a competitor relates to the client.

    :data:`UNCLASSIFIED` is the default for a candidate the classifier has not yet
    tiered; the classifier replaces it with one of the six real tiers.
    """

    UNCLASSIFIED = "unclassified"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ASPIRATIONAL = "aspirational"
    LUXURY_REFERENCE = "luxury_reference"
    INNOVATION_LEADER = "innovation_leader"
    CONVERSION_LEADER = "conversion_leader"


class CompetitorDimension(str, Enum):
    """The sixteen dimensions each competitor is profiled and benchmarked across."""

    BRAND_POSITIONING = "brand_positioning"
    VISUAL_LANGUAGE = "visual_language"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    NAVIGATION = "navigation"
    INFORMATION_ARCHITECTURE = "information_architecture"
    HOMEPAGE_STRUCTURE = "homepage_structure"
    COLLECTION_STRATEGY = "collection_strategy"
    PRODUCT_PAGE_STRATEGY = "product_page_strategy"
    TRUST_STRATEGY = "trust_strategy"
    CHECKOUT_STRATEGY = "checkout_strategy"
    MOBILE_STRATEGY = "mobile_strategy"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SEO = "seo"
    CONVERSION_PATTERNS = "conversion_patterns"


class ObservationSource(str, Enum):
    """Where a structured observation came from.

    Manual/analyst inputs today; the remaining values are the future data-source
    adapters (Firecrawl, Playwright, Browser/Figma MCP, Context7, OpenRouter),
    behind the data-source port. The domain treats them all identically.
    """

    MANUAL = "manual"
    ANALYST = "analyst"
    FIRECRAWL = "firecrawl"
    PLAYWRIGHT = "playwright"
    BROWSER_MCP = "browser_mcp"
    FIGMA_MCP = "figma_mcp"
    CONTEXT7 = "context7"
    OPENROUTER = "openrouter"
    OTHER = "other"


class PatternKind(str, Enum):
    """The category a recurring pattern belongs to."""

    UX = "ux"
    CRO = "cro"
    TRUST = "trust"
    VISUAL = "visual"
    NAVIGATION = "navigation"
    CONTENT = "content"
    MERCHANDISING = "merchandising"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    SEO = "seo"


class RecommendationAction(str, Enum):
    """What to do about a pattern or gap."""

    ADOPT = "adopt"
    AVOID = "avoid"
    MONITOR = "monitor"


class PrevalenceBand(str, Enum):
    """A categorical band for how common a pattern is across competitors."""

    UBIQUITOUS = "ubiquitous"
    COMMON = "common"
    EMERGING = "emerging"
    RARE = "rare"


class BenchmarkBand(str, Enum):
    """A competitor's standing on a dimension relative to the category benchmark."""

    LEADER = "leader"
    PARITY = "parity"
    LAGGARD = "laggard"

    @classmethod
    def from_relative(cls, score: Score, benchmark: Score) -> BenchmarkBand:
        """Classify ``score`` against a category ``benchmark``.

        ``>= benchmark`` is a LEADER; ``>= 0.75 × benchmark`` is PARITY; below that
        is a LAGGARD. Deterministic.
        """
        if benchmark.value <= 0:
            return cls.LEADER if score.value > 0 else cls.PARITY
        if score.value >= benchmark.value:
            return cls.LEADER
        if score.value >= 0.75 * benchmark.value:
            return cls.PARITY
        return cls.LAGGARD


class ConfidenceBand(str, Enum):
    """A categorical band for a confidence value."""

    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class Severity(IntEnum):
    """How damaging a risk/gap is (ordered)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Likelihood(IntEnum):
    """How probable a risk is (ordered)."""

    RARE = 1
    POSSIBLE = 2
    LIKELY = 3
    ALMOST_CERTAIN = 4


@dataclass(frozen=True, slots=True, order=True)
class Score:
    """A normalized benchmark score in ``[0, 100]``.

    Orders by value, so scores are directly comparable. The categorical
    :class:`BenchmarkBand` is derived *relative to a benchmark* via
    :meth:`BenchmarkBand.from_relative`, not from the number alone.
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidCompetitiveValueError(
                "Score.value must be within [0, 100].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        """Construct from a value clamped into ``[0, 100]`` (never raises)."""
        return cls(value=min(100.0, max(0.0, value)))

    @classmethod
    def zero(cls) -> Self:
        return cls(value=0.0)

    @classmethod
    def full(cls) -> Self:
        return cls(value=100.0)


@dataclass(frozen=True, slots=True)
class Prevalence:
    """How common a pattern is: ``count`` of ``total`` competitors exhibit it.

    Attributes:
        count: Competitors exhibiting the pattern (``>= 0``).
        total: Competitors examined (``>= 1``, and ``>= count``).
    """

    count: int
    total: int

    def __post_init__(self) -> None:
        if self.total < 1:
            raise InvalidCompetitiveValueError(
                "Prevalence.total must be >= 1.", details={"total": self.total}
            )
        if self.count < 0 or self.count > self.total:
            raise InvalidCompetitiveValueError(
                "Prevalence.count must be within [0, total].",
                details={"count": self.count, "total": self.total},
            )

    @property
    def ratio(self) -> float:
        """The fraction of competitors exhibiting the pattern."""
        return self.count / self.total

    @property
    def band(self) -> PrevalenceBand:
        """The categorical prevalence band."""
        r = self.ratio
        if r >= 0.75:
            return PrevalenceBand.UBIQUITOUS
        if r >= 0.5:
            return PrevalenceBand.COMMON
        if r >= 0.25:
            return PrevalenceBand.EMERGING
        return PrevalenceBand.RARE

    @property
    def is_dominant(self) -> bool:
        """Whether at least half the category exhibits the pattern."""
        return self.ratio >= 0.5


@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """A confidence value in ``[0, 1]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidCompetitiveValueError(
                "Confidence.value must be within [0, 1].", details={"value": self.value}
            )

    @property
    def band(self) -> ConfidenceBand:
        if self.value >= 0.85:
            return ConfidenceBand.VERY_HIGH
        if self.value >= 0.7:
            return ConfidenceBand.HIGH
        if self.value >= 0.5:
            return ConfidenceBand.MODERATE
        if self.value >= 0.3:
            return ConfidenceBand.LOW
        return ConfidenceBand.VERY_LOW

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(1.0, max(0.0, value)))
