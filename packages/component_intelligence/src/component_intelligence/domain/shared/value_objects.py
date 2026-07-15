"""Shared value objects for the Component Intelligence Engine.

These immutable, self-validating value objects are the vocabulary the engine reasons in: the
provenance of the evidence it cites, the forty-one supported components, their atomic level and
page affinity, the four purposes and the impacts it grades them on, the compatibility kinds and
inclusion states, the rule/region/visibility taxonomies, the interaction/animation/data kinds,
the component states and graph kinds, and the calibrated scales it scores on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, and no import of any provider or other engine —
those are reached only through ports. This engine decides *which components and why*; nothing
here is component code, a Figma node, or a rendered value.

Testing considerations
----------------------
* :class:`ComponentType` has the forty-one supported components; :class:`PageType` ten;
  :class:`GraphKind` exactly two.
* :class:`Confidence`, :class:`Score`, :class:`Percentage`, and :class:`Priority` validate
  their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AnimationKind",
    "AtomicLevel",
    "Breakpoint",
    "CompatibilityKind",
    "ComponentStateKind",
    "ComponentType",
    "CompositionRuleKind",
    "Confidence",
    "ConsideredAlternative",
    "DataKind",
    "EffectLevel",
    "GraphKind",
    "GraphRelation",
    "IOKind",
    "ImpactDimension",
    "ImpactLevel",
    "Inclusion",
    "InteractionKind",
    "InvalidCIValueError",
    "NodeKind",
    "PageType",
    "Percentage",
    "PlacementRegion",
    "Priority",
    "ProvenanceKind",
    "PurposeKind",
    "QualityBand",
    "Rank",
    "ResponsiveIntent",
    "Score",
    "Tag",
    "VisibilityKind",
]


class InvalidCIValueError(DesignDirectorError):
    """Raised when a Component Intelligence value object is constructed with invalid data."""

    code = "invalid_component_intelligence_value"
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
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    FIGMA = "figma"
    ANALYTICS = "analytics"


# --------------------------------------------------------------------------- #
# Components & pages                                                            #
# --------------------------------------------------------------------------- #
class ComponentType(str, Enum):
    """One of the forty-one supported components."""

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
    """One of the ten supported page types (aligned with the wireframe plan)."""

    HOMEPAGE = "homepage"
    COLLECTION = "collection"
    PRODUCT = "product"
    CART = "cart"
    CHECKOUT = "checkout"
    SEARCH = "search"
    ACCOUNT = "account"
    BLOG = "blog"
    LANDING = "landing"
    CMS = "cms"


class AtomicLevel(str, Enum):
    """The atomic-design level of a component."""

    ATOM = "atom"
    MOLECULE = "molecule"
    ORGANISM = "organism"
    TEMPLATE = "template"


# --------------------------------------------------------------------------- #
# Purpose, impact, effect                                                      #
# --------------------------------------------------------------------------- #
class PurposeKind(str, Enum):
    """One of the four purposes every component must serve."""

    BUSINESS = "business"
    USER = "user"
    CONVERSION = "conversion"
    TRUST = "trust"


class ImpactDimension(str, Enum):
    """A non-functional dimension a component is graded on."""

    SEO = "seo"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"


class ImpactLevel(str, Enum):
    """The impact a component has on an SEO/accessibility/performance dimension."""

    STRONG_POSITIVE = "strong_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EffectLevel(str, Enum):
    """The strength of a component's effect on conversion, friction, or trust."""

    STRONG = "strong"
    MODERATE = "moderate"
    SLIGHT = "slight"
    NONE = "none"


# --------------------------------------------------------------------------- #
# Inclusion, compatibility                                                     #
# --------------------------------------------------------------------------- #
class Inclusion(str, Enum):
    """Whether a component is part of the composition."""

    INCLUDED = "included"
    OPTIONAL = "optional"
    EXCLUDED = "excluded"


class CompatibilityKind(str, Enum):
    """A typed relationship between two components."""

    REQUIRES = "requires"
    CONFLICTS_WITH = "conflicts_with"
    ENHANCES = "enhances"
    REPLACES = "replaces"


# --------------------------------------------------------------------------- #
# Rules, regions, visibility, behaviour                                        #
# --------------------------------------------------------------------------- #
class CompositionRuleKind(str, Enum):
    """A dimension a composition rule governs."""

    ORDER = "order"
    GROUPING = "grouping"
    HIERARCHY = "hierarchy"
    DENSITY = "density"


class PlacementRegion(str, Enum):
    """Where on a page a component is placed."""

    HEADER = "header"
    ABOVE_FOLD = "above_fold"
    MAIN = "main"
    SIDEBAR = "sidebar"
    BELOW_FOLD = "below_fold"
    FOOTER = "footer"
    STICKY = "sticky"
    OVERLAY = "overlay"


class VisibilityKind(str, Enum):
    """When a component is visible."""

    ALWAYS = "always"
    MOBILE_ONLY = "mobile_only"
    DESKTOP_ONLY = "desktop_only"
    CONDITIONAL = "conditional"
    HIDDEN = "hidden"


class Breakpoint(str, Enum):
    """A responsive breakpoint band (named, not pixel-bound)."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WIDE = "wide"


class ResponsiveIntent(str, Enum):
    """How a component behaves at a breakpoint (behaviour, not a layout spec)."""

    STACK = "stack"
    REFLOW = "reflow"
    HIDE = "hide"
    COLLAPSE = "collapse"
    REORDER = "reorder"
    CAROUSEL = "carousel"
    STICKY = "sticky"
    RETAIN = "retain"


class InteractionKind(str, Enum):
    """An interaction behaviour a component supports (intent, not visual treatment)."""

    CLICK = "click"
    HOVER = "hover"
    EXPAND_COLLAPSE = "expand_collapse"
    DRAG = "drag"
    SWIPE = "swipe"
    SUBMIT = "submit"
    FILTER = "filter"
    SORT = "sort"
    ADD_TO_CART = "add_to_cart"
    ZOOM = "zoom"
    PAGINATE = "paginate"
    INFINITE_SCROLL = "infinite_scroll"
    AUTOCOMPLETE = "autocomplete"
    DRAWER_TOGGLE = "drawer_toggle"


class AnimationKind(str, Enum):
    """A restrained animation posture a component may use."""

    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    SCALE = "scale"
    SKELETON = "skeleton"


class DataKind(str, Enum):
    """A kind of data a component needs or produces."""

    PRODUCT = "product"
    PRODUCT_LIST = "product_list"
    COLLECTION = "collection"
    PRICE = "price"
    INVENTORY = "inventory"
    REVIEW = "review"
    RATING = "rating"
    CART = "cart"
    ORDER = "order"
    CUSTOMER = "customer"
    CONTENT = "content"
    NAVIGATION = "navigation"
    SEARCH_RESULT = "search_result"
    FACET = "facet"
    RECOMMENDATION = "recommendation"
    MEDIA = "media"


class IOKind(str, Enum):
    """The kind of artifact a component produces."""

    DATA = "data"
    EVENT = "event"
    STATE = "state"
    ARTIFACT = "artifact"


class ComponentStateKind(str, Enum):
    """A UI state a component must handle."""

    DEFAULT = "default"
    HOVER = "hover"
    ACTIVE = "active"
    FOCUS = "focus"
    DISABLED = "disabled"
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"
    SUCCESS = "success"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the two component graphs."""

    COMPONENT = "component"
    DEPENDENCY = "dependency"


class NodeKind(str, Enum):
    """The kind of node a component-graph node represents."""

    COMPONENT = "component"
    SUBCOMPONENT = "subcomponent"
    PAGE = "page"
    DATA = "data"


class GraphRelation(str, Enum):
    """A typed, directed edge between two component-graph nodes.

    ``CONTAINS``, ``DEPENDS_ON``, and ``REQUIRES`` must be acyclic (a component cannot
    transitively require itself). ``CONFLICTS_WITH`` and ``ENHANCES`` may be mutual.
    """

    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    ENHANCES = "enhances"
    CONFLICTS_WITH = "conflicts_with"
    REPLACES = "replaces"
    PLACED_ON = "placed_on"
    CONSUMES = "consumes"


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
            raise InvalidCIValueError(
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
            raise InvalidCIValueError(
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
            raise InvalidCIValueError(
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
        raise InvalidCIValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidCIValueError(
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
            raise InvalidCIValueError("Rank must be an int >= 1.", details={"value": self.value})

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A component the engine weighed and rejected — the trade-off record.

    A Shopify/Apple-calibre design team never adds a component without knowing what it chose
    it over. Recording the considered alternative makes each inclusion a deliberate,
    defensible decision rather than a default.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidCIValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidCIValueError(
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
            raise InvalidCIValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
