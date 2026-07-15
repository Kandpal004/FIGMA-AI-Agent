"""Shared value objects for the Design Orchestrator Engine.

These immutable, self-validating value objects are the vocabulary the orchestrator plans in: the
provenance of the evidence it cites, the ten pages and forty-one components it orders, the
section roles and layout modes it chooses, the responsive breakpoints and target platforms, the
kinds of execution step it sequences and tree node it nests, the review gates it schedules, the
kinds of graph it builds, and the calibrated scales it scores on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, and no import of any provider or other engine —
those are reached only through ports. This engine plans the *execution*; it renders no UI and no
Figma.

Testing considerations
----------------------
* :class:`ExecutionStepKind` and :class:`TreeNodeKind` have the expected members;
  :class:`GraphKind` has exactly two (execution, layout).
* :class:`Confidence`, :class:`Score`, :class:`Percentage`, and :class:`Priority` validate their
  ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "Alignment",
    "Breakpoint",
    "CheckpointStatus",
    "ComponentType",
    "Confidence",
    "ConsideredAlternative",
    "Density",
    "ExecutionStepKind",
    "GraphKind",
    "GraphRelation",
    "InvalidDOValueError",
    "LayoutMode",
    "LayoutRegionKind",
    "NodeKind",
    "PageType",
    "Percentage",
    "Platform",
    "Priority",
    "ProvenanceKind",
    "Rank",
    "ReviewGateKind",
    "Score",
    "SectionRole",
    "Tag",
    "ThemeMode",
    "TreeNodeKind",
    "QualityBand",
]


class InvalidDOValueError(DesignDirectorError):
    """Raised when a Design Orchestrator value object is constructed with invalid data."""

    code = "invalid_design_orchestrator_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates — the eleven upstream engines."""

    BUSINESS_STRATEGY = "business_strategy"
    BRAND_STRATEGY = "brand_strategy"
    PSYCHOLOGY = "psychology"
    UX_STRATEGY = "ux_strategy"
    INFORMATION_ARCHITECTURE = "information_architecture"
    WIREFRAME = "wireframe"
    CREATIVE_DIRECTOR = "creative_director"
    DESIGN_LANGUAGE = "design_language"
    COMPONENT_INTELLIGENCE = "component_intelligence"
    DESIGN_SYSTEM = "design_system"
    KNOWLEDGE = "knowledge"
    FIGMA = "figma"
    ANALYTICS = "analytics"


# --------------------------------------------------------------------------- #
# Pages & components                                                           #
# --------------------------------------------------------------------------- #
class PageType(str, Enum):
    """One of the ten supported page types (aligned with the Design System)."""

    HOMEPAGE = "homepage"
    COLLECTION = "collection"
    PRODUCT = "product"
    CART = "cart"
    CHECKOUT = "checkout"
    SEARCH = "search"
    BLOG = "blog"
    ACCOUNT = "account"
    LANDING = "landing"
    CMS = "cms"


class ComponentType(str, Enum):
    """One of the forty-one supported components (aligned with Component Intelligence)."""

    ANNOUNCEMENT_BAR = "announcement_bar"
    HEADER = "header"
    MEGA_MENU = "mega_menu"
    NAVIGATION = "navigation"
    BREADCRUMBS = "breadcrumbs"
    HERO = "hero"
    HERO_CAROUSEL = "hero_carousel"
    CATEGORY_GRID = "category_grid"
    COLLECTION_GRID = "collection_grid"
    PRODUCT_GRID = "product_grid"
    PRODUCT_CARD = "product_card"
    PRODUCT_GALLERY = "product_gallery"
    PRODUCT_INFORMATION = "product_information"
    VARIANT_PICKER = "variant_picker"
    STICKY_ADD_TO_CART = "sticky_add_to_cart"
    SIZE_GUIDE = "size_guide"
    DELIVERY_WIDGET = "delivery_widget"
    TRUST_BADGES = "trust_badges"
    USP_GRID = "usp_grid"
    TESTIMONIALS = "testimonials"
    REVIEWS = "reviews"
    FAQ = "faq"
    COMPARISON_TABLE = "comparison_table"
    RECENTLY_VIEWED = "recently_viewed"
    RELATED_PRODUCTS = "related_products"
    RECOMMENDATIONS = "recommendations"
    BUNDLE_BUILDER = "bundle_builder"
    CART_DRAWER = "cart_drawer"
    MINI_CART = "mini_cart"
    CHECKOUT_BLOCKS = "checkout_blocks"
    FOOTER = "footer"
    NEWSLETTER = "newsletter"
    BLOG_CARDS = "blog_cards"
    FORMS = "forms"
    SEARCH = "search"
    FILTERS = "filters"
    SORTING = "sorting"
    PAGINATION = "pagination"
    WISHLIST = "wishlist"
    ACCOUNT = "account"
    ORDER_TIMELINE = "order_timeline"


# --------------------------------------------------------------------------- #
# Sections & layout                                                            #
# --------------------------------------------------------------------------- #
class SectionRole(str, Enum):
    """The role a section plays on a page."""

    HEADER = "header"
    HERO = "hero"
    NAVIGATION = "navigation"
    CONTENT = "content"
    CONVERSION = "conversion"
    TRUST = "trust"
    DISCOVERY = "discovery"
    FORM = "form"
    FOOTER = "footer"


class LayoutMode(str, Enum):
    """How a section arranges its content."""

    STACK = "stack"
    GRID = "grid"
    SPLIT = "split"
    FULL_BLEED = "full_bleed"


class Alignment(str, Enum):
    """Content alignment within a section."""

    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class Density(str, Enum):
    """Spacing density of a section."""

    COMPACT = "compact"
    REGULAR = "regular"
    SPACIOUS = "spacious"


class LayoutRegionKind(str, Enum):
    """The kind of layout region on a page."""

    HEADER = "header"
    MAIN = "main"
    ASIDE = "aside"
    FOOTER = "footer"
    SECTION = "section"


class Breakpoint(str, Enum):
    """A responsive breakpoint band."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WIDE = "wide"


class Platform(str, Enum):
    """A target platform the plan is realised on."""

    GENERIC = "generic"
    SHOPIFY = "shopify"
    MAGENTO = "magento"


class ThemeMode(str, Enum):
    """A theme mode a visual choice targets."""

    LIGHT = "light"
    DARK = "dark"


# --------------------------------------------------------------------------- #
# Execution & tree                                                            #
# --------------------------------------------------------------------------- #
class ExecutionStepKind(str, Enum):
    """A step in the deterministic execution graph (the P18 replay script)."""

    SETUP_THEME = "setup_theme"
    SETUP_TOKENS = "setup_tokens"
    BUILD_PAGE = "build_page"
    PLACE_SECTION = "place_section"
    INSTANTIATE_COMPONENT = "instantiate_component"
    APPLY_VARIANT = "apply_variant"
    APPLY_RESPONSIVE = "apply_responsive"
    APPLY_ACCESSIBILITY = "apply_accessibility"
    REVIEW_GATE = "review_gate"


class TreeNodeKind(str, Enum):
    """The kind of node in the component tree."""

    ROOT = "root"
    PAGE = "page"
    SECTION = "section"
    COMPONENT = "component"
    VARIANT = "variant"


# --------------------------------------------------------------------------- #
# Review                                                                       #
# --------------------------------------------------------------------------- #
class ReviewGateKind(str, Enum):
    """A review checkpoint scheduled before Figma generation."""

    TOKENS_APPROVED = "tokens_approved"
    LAYOUT_APPROVED = "layout_approved"
    ACCESSIBILITY_APPROVED = "accessibility_approved"
    PERFORMANCE_APPROVED = "performance_approved"
    PRE_GENERATION = "pre_generation"


class CheckpointStatus(str, Enum):
    """The status of a scheduled checkpoint (the plan schedules; it does not run reviews)."""

    PENDING = "pending"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the two orchestrator graphs."""

    EXECUTION = "execution"
    LAYOUT = "layout"


class NodeKind(str, Enum):
    """The kind of node an orchestrator-graph node represents."""

    STEP = "step"
    REGION = "region"
    PAGE = "page"
    SECTION = "section"
    COMPONENT = "component"


class GraphRelation(str, Enum):
    """A typed, directed edge between two orchestrator-graph nodes.

    ``PRECEDES``, ``DEPENDS_ON`` and ``CONTAINS`` must be acyclic — the execution order and the
    region containment form no cycle.
    """

    PRECEDES = "precedes"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    PLACES = "places"
    BINDS = "binds"


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
            raise InvalidDOValueError(
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
            raise InvalidDOValueError(
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
            raise InvalidDOValueError(
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
        raise InvalidDOValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidDOValueError(
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
class Rank:
    """A 1-based ordinal rank (1 = first)."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 1:
            raise InvalidDOValueError("Rank must be an int >= 1.", details={"value": self.value})

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A choice the orchestrator weighed and rejected — the trade-off record.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidDOValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidDOValueError(
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
            raise InvalidDOValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
