"""Shared value objects for the Design System Engine.

These immutable, self-validating value objects are the vocabulary the engine specifies in: the
provenance of the evidence it cites, the token categories and the three token tiers, the
forty-one components and ten pages it maps, the atomic levels, the theme modes and text
directions, the ten UI states, the breakpoints and target platforms, the property and
constraint kinds, the kinds of graph it builds, and the calibrated scales it scores on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, and no import of any provider or other engine —
those are reached only through ports. This engine produces the design-system *specification*
(the token graph, component specs, themes, constraints, platform mappings); it renders no UI and
no Figma.

Testing considerations
----------------------
* :class:`TokenTier` has exactly three members, :class:`ComponentType` the forty-one components,
  :class:`PageType` ten, :class:`GraphKind` exactly six.
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
    "AtomicLevel",
    "Breakpoint",
    "ComponentType",
    "Confidence",
    "ConsideredAlternative",
    "ConstraintKind",
    "Direction",
    "EnforcementLevel",
    "GraphKind",
    "GraphRelation",
    "InvalidDSValueError",
    "NodeKind",
    "PageType",
    "Percentage",
    "Platform",
    "Priority",
    "PropertyType",
    "ProvenanceKind",
    "QualityBand",
    "Rank",
    "Ratio",
    "Score",
    "StateKind",
    "Tag",
    "ThemeMode",
    "TokenCategory",
    "TokenTier",
]


class InvalidDSValueError(DesignDirectorError):
    """Raised when a Design System value object is constructed with invalid data."""

    code = "invalid_design_system_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates — the ten upstream engines."""

    DESIGN_LANGUAGE = "design_language"
    COMPONENT_INTELLIGENCE = "component_intelligence"
    CREATIVE_DIRECTOR = "creative_director"
    BUSINESS_STRATEGY = "business_strategy"
    BRAND_STRATEGY = "brand_strategy"
    PSYCHOLOGY = "psychology"
    UX_STRATEGY = "ux_strategy"
    INFORMATION_ARCHITECTURE = "information_architecture"
    WIREFRAME = "wireframe"
    KNOWLEDGE = "knowledge"
    FIGMA = "figma"
    ANALYTICS = "analytics"


# --------------------------------------------------------------------------- #
# Tokens                                                                        #
# --------------------------------------------------------------------------- #
class TokenCategory(str, Enum):
    """The category a design token belongs to."""

    COLOR = "color"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    RADIUS = "radius"
    SHADOW = "shadow"
    ELEVATION = "elevation"
    BORDER = "border"
    MOTION = "motion"
    ANIMATION = "animation"
    INTERACTION = "interaction"
    BREAKPOINT = "breakpoint"
    GRID = "grid"
    CONTAINER = "container"
    ICON = "icon"
    ILLUSTRATION = "illustration"
    Z_INDEX = "z_index"
    OPACITY = "opacity"
    STATE = "state"


class TokenTier(str, Enum):
    """The tier of a token in the three-tier architecture."""

    PRIMITIVE = "primitive"
    SEMANTIC = "semantic"
    COMPONENT = "component"


# --------------------------------------------------------------------------- #
# Components & pages                                                            #
# --------------------------------------------------------------------------- #
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


class PageType(str, Enum):
    """One of the ten supported page types."""

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


class AtomicLevel(str, Enum):
    """The atomic-design level of a component."""

    ATOM = "atom"
    MOLECULE = "molecule"
    ORGANISM = "organism"
    TEMPLATE = "template"
    PAGE = "page"


# --------------------------------------------------------------------------- #
# Themes, direction, states                                                    #
# --------------------------------------------------------------------------- #
class ThemeMode(str, Enum):
    """A theme mode."""

    LIGHT = "light"
    DARK = "dark"


class Direction(str, Enum):
    """A text/layout direction."""

    LTR = "ltr"
    RTL = "rtl"


class StateKind(str, Enum):
    """A UI state a component must handle."""

    DEFAULT = "default"
    HOVER = "hover"
    FOCUS = "focus"
    ACTIVE = "active"
    DISABLED = "disabled"
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"


class Breakpoint(str, Enum):
    """A responsive breakpoint band."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WIDE = "wide"


class Platform(str, Enum):
    """A target platform a component maps to."""

    GENERIC = "generic"
    SHOPIFY = "shopify"
    MAGENTO = "magento"


class PropertyType(str, Enum):
    """The type of a component property."""

    VARIANT = "variant"
    BOOLEAN = "boolean"
    TEXT = "text"
    TOKEN = "token"
    NUMBER = "number"


# --------------------------------------------------------------------------- #
# Constraints                                                                   #
# --------------------------------------------------------------------------- #
class ConstraintKind(str, Enum):
    """A rule the design system enforces on every future UI."""

    TOKEN_ONLY = "token_only"
    NO_HARDCODED = "no_hardcoded"
    SPACING_GRID = "spacing_grid"
    TYPE_SCALE = "type_scale"
    CONTRAST_MIN = "contrast_min"
    RTL_MIRROR = "rtl_mirror"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    THEME_PARITY = "theme_parity"


class EnforcementLevel(str, Enum):
    """How strictly a constraint is enforced."""

    BLOCKING = "blocking"
    RECOMMENDED = "recommended"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the six design-system graphs."""

    TOKEN = "token"
    COMPONENT = "component"
    VARIANT = "variant"
    THEME = "theme"
    CONSTRAINT = "constraint"
    DEPENDENCY = "dependency"


class NodeKind(str, Enum):
    """The kind of node a design-system-graph node represents."""

    TOKEN = "token"
    COMPONENT = "component"
    VARIANT = "variant"
    STATE = "state"
    THEME = "theme"
    CONSTRAINT = "constraint"
    PLATFORM = "platform"


class GraphRelation(str, Enum):
    """A typed, directed edge between two design-system-graph nodes.

    ``ALIASES``, ``DERIVES_FROM`` and ``DEPENDS_ON`` must be acyclic — a token cannot
    transitively alias itself, and a component cannot transitively depend on itself.
    """

    ALIASES = "aliases"
    DERIVES_FROM = "derives_from"
    USES = "uses"
    HAS_VARIANT = "has_variant"
    HAS_STATE = "has_state"
    THEMES = "themes"
    CONSTRAINS = "constrains"
    DEPENDS_ON = "depends_on"
    MAPS_TO = "maps_to"


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
            raise InvalidDSValueError(
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
            raise InvalidDSValueError(
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
            raise InvalidDSValueError(
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
        raise InvalidDSValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidDSValueError(
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
class Ratio:
    """A modular ratio greater than 1 (e.g. a type scale ratio like 1.25)."""

    value: float

    def __post_init__(self) -> None:
        if not self.value > 1.0:
            raise InvalidDSValueError(
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
            raise InvalidDSValueError("Rank must be an int >= 1.", details={"value": self.value})

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A choice the engine weighed and rejected — the trade-off record.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidDSValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidDSValueError(
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
            raise InvalidDSValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
