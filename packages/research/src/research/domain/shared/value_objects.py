"""Shared value objects for the Research Engine.

These immutable, self-validating value objects are the vocabulary the engine
reasons in: the kinds of source it draws from, the providers behind them, the kinds
of raw artifact it collects, the entity and relationship types it extracts, and the
calibrated scales it uses to measure confidence, quality, freshness, and
completeness.

Everything here is pure domain: only the standard library and the shared-kernel
error base (:mod:`core.errors`). No framework, no I/O, no global mutable state, and
no import of any provider or downstream engine — those are reached only through
ports, keeping this domain independent.

Testing considerations
----------------------
* :class:`EntityType` has exactly nineteen members (the required entity taxonomy).
* :class:`Confidence`, :class:`QualityScore`, :class:`Freshness`, and
  :class:`Completeness` validate their ranges, order by value, and derive bands.
* :class:`Freshness.from_age` and :class:`Completeness.from_counts` are deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "ArtifactKind",
    "Completeness",
    "Confidence",
    "EntityType",
    "InvalidResearchValueError",
    "ProviderKind",
    "Freshness",
    "QualityBand",
    "QualityScore",
    "RelationshipType",
    "ResearchCategory",
    "SourceKind",
    "Tag",
]


class InvalidResearchValueError(DesignDirectorError):
    """Raised when a research value object is constructed with invalid data."""

    code = "invalid_research_value"
    http_status = 422


class SourceKind(str, Enum):
    """The kinds of source the engine can research."""

    BUSINESS_WEBSITE = "business_website"
    COMPETITOR_WEBSITE = "competitor_website"
    BRAND_GUIDELINES = "brand_guidelines"
    DESIGN_SYSTEM = "design_system"
    KNOWLEDGE_ENGINE = "knowledge_engine"
    PROJECT_MEMORY = "project_memory"
    USER_DOCUMENT = "user_document"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    BROWSER_SESSION = "browser_session"


class ProviderKind(str, Enum):
    """The provider (adapter) that fulfils a source or extraction.

    Manual/in-memory and the internal engines today; the rest are future external
    providers behind the same ports.
    """

    MANUAL = "manual"
    IN_MEMORY = "in_memory"
    KNOWLEDGE_ENGINE = "knowledge_engine"
    PROJECT_MEMORY = "project_memory"
    HTML_PARSER = "html_parser"
    STRUCTURED = "structured"
    FIRECRAWL = "firecrawl"
    PLAYWRIGHT_MCP = "playwright_mcp"
    BROWSER_MCP = "browser_mcp"
    FIGMA_MCP = "figma_mcp"
    CONTEXT7 = "context7"
    OPENROUTER = "openrouter"
    SEARCH = "search"
    VISION = "vision"
    OTHER = "other"


class ArtifactKind(str, Enum):
    """The form of a collected raw artifact."""

    HTML = "html"
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    STRUCTURED = "structured"
    BINARY = "binary"


class ResearchCategory(str, Enum):
    """The category a research result belongs to (also the future research areas)."""

    WEBSITE = "website"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    DESIGN = "design"
    BRAND = "brand"
    PRODUCT = "product"
    COMPETITOR = "competitor"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"


class EntityType(str, Enum):
    """The nineteen entity types the engine extracts."""

    BRAND = "brand"
    PRODUCT = "product"
    COLLECTION = "collection"
    CATEGORY = "category"
    NAVIGATION = "navigation"
    SECTION = "section"
    CTA = "cta"
    TYPOGRAPHY = "typography"
    COLOR = "color"
    LAYOUT = "layout"
    TRUST_ELEMENT = "trust_element"
    FAQ = "faq"
    REVIEW = "review"
    PRICING = "pricing"
    CHECKOUT = "checkout"
    POLICY = "policy"
    FOOTER = "footer"
    COMPONENT = "component"
    DESIGN_PATTERN = "design_pattern"


class RelationshipType(str, Enum):
    """The typed edges between extracted entities."""

    CONTAINS = "contains"
    PART_OF = "part_of"
    LINKS_TO = "links_to"
    HAS_CTA = "has_cta"
    HAS_PRICING = "has_pricing"
    HAS_REVIEW = "has_review"
    USES_TYPOGRAPHY = "uses_typography"
    USES_COLOR = "uses_color"
    BELONGS_TO = "belongs_to"
    REFERENCES = "references"
    DESCRIBES = "describes"
    PRECEDES = "precedes"
    SIMILAR_TO = "similar_to"
    RELATED_TO = "related_to"


class QualityBand(str, Enum):
    """A categorical band shared by the quality/score scales."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """A confidence value in ``[0, 1]``."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidResearchValueError(
                "Confidence.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(1.0, max(0.0, value)))


@dataclass(frozen=True, slots=True, order=True)
class QualityScore:
    """A quality score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidResearchValueError(
                "QualityScore.value must be within [0, 100].", details={"value": self.value}
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


@dataclass(frozen=True, slots=True, order=True)
class Freshness:
    """How fresh data is, in ``[0, 1]`` (1 = just collected, 0 = fully stale)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidResearchValueError(
                "Freshness.value must be within [0, 1].", details={"value": self.value}
            )

    @property
    def is_fresh(self) -> bool:
        return self.value >= 0.66

    @classmethod
    def from_age(cls, age_days: float, *, stale_after_days: float = 30.0) -> Self:
        """Deterministic linear decay: fresh at age 0, stale at ``stale_after_days``."""
        if stale_after_days <= 0:
            return cls(value=0.0)
        return cls(value=min(1.0, max(0.0, 1.0 - age_days / stale_after_days)))


@dataclass(frozen=True, slots=True, order=True)
class Completeness:
    """How complete a result is, in ``[0, 1]`` (fraction of expected fields present)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidResearchValueError(
                "Completeness.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def from_counts(cls, present: int, expected: int) -> Self:
        """The fraction ``present / expected`` (1.0 when nothing is expected)."""
        if expected <= 0:
            return cls(value=1.0)
        return cls(value=min(1.0, max(0.0, present / expected)))


_TAG_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Tag:
    """A normalized free-form label (lower case, whitespace collapsed to hyphens)."""

    value: str

    def __post_init__(self) -> None:
        normalized = _TAG_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidResearchValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
