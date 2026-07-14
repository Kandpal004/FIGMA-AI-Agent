"""Shared value objects for the Wireframe Planning Engine.

These immutable, self-validating value objects are the vocabulary the engine plans in: the
provenance of the evidence it cites, the page types it structures, the section and block
taxonomy it lays out, the components it requires, the interaction/responsive/accessibility/
SEO/performance requirement kinds it records, the approval gates it derives, the kinds of
graph it builds, and the calibrated scales it scores everything on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, no global mutable state, and no import of any
provider or other engine — those are reached only through ports, keeping this domain
independent. This engine plans; it draws nothing. Nothing in this vocabulary encodes a
visual property (no colour, font, coordinate, or pixel) — only *what* must be built, *why*,
*from what*, *in what order*, and *how it is approved*.

Testing considerations
----------------------
* :class:`PageType` has exactly ten members (the supported page taxonomy) and
  :class:`GraphKind` exactly six.
* :class:`Confidence`, :class:`WFScore`, :class:`Percentage`, and :class:`Priority`
  validate their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AccessibilityKind",
    "ApprovalGate",
    "ApproverRole",
    "AssetKind",
    "BlockKind",
    "Breakpoint",
    "ComponentKind",
    "Confidence",
    "ConsideredAlternative",
    "DataKind",
    "GraphKind",
    "GraphRelation",
    "IOKind",
    "InteractionKind",
    "InvalidWireframeValueError",
    "NodeKind",
    "PageType",
    "Percentage",
    "PerformanceKind",
    "Priority",
    "ProvenanceKind",
    "QualityBand",
    "Rank",
    "RequirementLevel",
    "ResponsiveIntent",
    "SEOKind",
    "SectionType",
    "Tag",
    "WFScore",
]


class InvalidWireframeValueError(DesignDirectorError):
    """Raised when a wireframe value object is constructed with invalid data."""

    code = "invalid_wireframe_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The nine upstream engines the planner consumes today; future feedback sources (design
    analytics, Figma review feedback) extend this additively.
    """

    INFORMATION_ARCHITECTURE = "information_architecture"
    UX_STRATEGY = "ux_strategy"
    BUSINESS_STRATEGY = "business_strategy"
    BRAND_STRATEGY = "brand_strategy"
    PSYCHOLOGY = "psychology"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    REASONING = "reasoning"
    ANALYTICS = "analytics"
    FIGMA_FEEDBACK = "figma_feedback"


# --------------------------------------------------------------------------- #
# Pages, sections, blocks, components                                          #
# --------------------------------------------------------------------------- #
class PageType(str, Enum):
    """One of the ten supported page types."""

    HOMEPAGE = "homepage"
    COLLECTION = "collection"
    PRODUCT = "product"
    CART = "cart"
    CHECKOUT = "checkout"
    LANDING = "landing"
    BLOG = "blog"
    SEARCH = "search"
    ACCOUNT = "account"
    CMS = "cms"


class SectionType(str, Enum):
    """A structural section a page plan can contain (ecommerce planning taxonomy).

    The Wireframe engine owns this taxonomy; the IA adapter maps Phase-11 section types onto
    it, keeping the bounded context isolated.
    """

    HERO = "hero"
    VALUE_PROPOSITION = "value_proposition"
    FEATURED_PRODUCTS = "featured_products"
    CATEGORY_GRID = "category_grid"
    PRODUCT_GALLERY = "product_gallery"
    PRODUCT_INFO = "product_info"
    BUY_BOX = "buy_box"
    VARIANT_SELECTOR = "variant_selector"
    PRICING = "pricing"
    REVIEWS = "reviews"
    RATINGS_SUMMARY = "ratings_summary"
    TRUST = "trust"
    GUARANTEE = "guarantee"
    FAQ = "faq"
    SPECIFICATIONS = "specifications"
    RECOMMENDATIONS = "recommendations"
    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"
    RELATED_PRODUCTS = "related_products"
    SOCIAL_PROOF = "social_proof"
    FILTERS = "filters"
    SORT_BAR = "sort_bar"
    SEARCH_BAR = "search_bar"
    RESULTS_GRID = "results_grid"
    NO_RESULTS = "no_results"
    CART_SUMMARY = "cart_summary"
    CART_LINE_ITEMS = "cart_line_items"
    CHECKOUT_FORM = "checkout_form"
    ORDER_SUMMARY = "order_summary"
    PAYMENT = "payment"
    SHIPPING = "shipping"
    NEWSLETTER = "newsletter"
    CONTENT_BODY = "content_body"
    ARTICLE_LIST = "article_list"
    ARTICLE_BODY = "article_body"
    BREADCRUMBS = "breadcrumbs"
    GLOBAL_NAV = "global_nav"
    FOOTER = "footer"
    ACCOUNT_MENU = "account_menu"
    ORDER_HISTORY = "order_history"
    CONTACT_FORM = "contact_form"


class BlockKind(str, Enum):
    """The kind of block a section carries — the spec's planning block taxonomy."""

    CONTENT = "content"
    MEDIA = "media"
    TRUST = "trust"
    CTA = "cta"
    PRODUCT = "product"
    RECOMMENDATION = "recommendation"
    FAQ = "faq"
    REVIEW = "review"
    FOOTER = "footer"
    HERO = "hero"
    NAV = "nav"
    FORM = "form"
    BREADCRUMB = "breadcrumb"


class ComponentKind(str, Enum):
    """A planning-level component a section requires (what, not how it renders)."""

    PRODUCT_GALLERY = "product_gallery"
    PRODUCT_CARD = "product_card"
    ADD_TO_CART = "add_to_cart"
    PRICE = "price"
    VARIANT_SELECTOR = "variant_selector"
    QUANTITY_SELECTOR = "quantity_selector"
    REVIEW_SUMMARY = "review_summary"
    REVIEW_LIST = "review_list"
    RATING_STARS = "rating_stars"
    TRUST_BADGES = "trust_badges"
    GUARANTEE_BADGE = "guarantee_badge"
    RECOMMENDATION_CAROUSEL = "recommendation_carousel"
    FAQ_ACCORDION = "faq_accordion"
    BREADCRUMB = "breadcrumb"
    SEARCH_INPUT = "search_input"
    SEARCH_FACETS = "search_facets"
    SORT_DROPDOWN = "sort_dropdown"
    PAGINATION = "pagination"
    CART_LINE_ITEM = "cart_line_item"
    ORDER_SUMMARY = "order_summary"
    CHECKOUT_FORM = "checkout_form"
    PAYMENT_METHODS = "payment_methods"
    ADDRESS_FORM = "address_form"
    NEWSLETTER_FORM = "newsletter_form"
    FOOTER_COLUMNS = "footer_columns"
    NAV_MENU = "nav_menu"
    HERO_BANNER = "hero_banner"
    CATEGORY_TILE = "category_tile"
    ARTICLE_CARD = "article_card"
    MEDIA_PLAYER = "media_player"
    CONTENT_BLOCK = "content_block"


class RequirementLevel(str, Enum):
    """Whether an element is required for the page or optional."""

    REQUIRED = "required"
    OPTIONAL = "optional"


# --------------------------------------------------------------------------- #
# Section requirement kinds                                                    #
# --------------------------------------------------------------------------- #
class DataKind(str, Enum):
    """A kind of data a section needs supplied to be built."""

    PRODUCT = "product"
    PRODUCT_LIST = "product_list"
    COLLECTION = "collection"
    PRICE = "price"
    INVENTORY = "inventory"
    REVIEW = "review"
    RATING = "rating"
    RECOMMENDATION = "recommendation"
    CART = "cart"
    ORDER = "order"
    CUSTOMER = "customer"
    CONTENT = "content"
    ARTICLE = "article"
    FAQ = "faq"
    NAVIGATION = "navigation"
    SEARCH_RESULT = "search_result"
    FACET = "facet"


class AssetKind(str, Enum):
    """A kind of asset a section needs produced or sourced."""

    IMAGE = "image"
    VIDEO = "video"
    ICON = "icon"
    LOGO = "logo"
    ILLUSTRATION = "illustration"
    ANIMATION = "animation"
    DOCUMENT = "document"


class InteractionKind(str, Enum):
    """An interaction behaviour a section requires (intent, not visual treatment)."""

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
    VALIDATE = "validate"
    AUTOCOMPLETE = "autocomplete"


class ResponsiveIntent(str, Enum):
    """How a section should behave at a breakpoint (behaviour, not a layout spec)."""

    STACK = "stack"
    REFLOW = "reflow"
    HIDE_SECONDARY = "hide_secondary"
    COLLAPSE = "collapse"
    REORDER = "reorder"
    CAROUSEL = "carousel"
    STICKY = "sticky"
    RETAIN = "retain"


class Breakpoint(str, Enum):
    """A responsive breakpoint band (named, not pixel-bound)."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WIDE = "wide"


class AccessibilityKind(str, Enum):
    """An accessibility requirement a section must satisfy (WCAG intent)."""

    KEYBOARD = "keyboard"
    SCREEN_READER = "screen_reader"
    CONTRAST = "contrast"
    FOCUS_ORDER = "focus_order"
    ALT_TEXT = "alt_text"
    ARIA_LABEL = "aria_label"
    TOUCH_TARGET = "touch_target"
    REDUCED_MOTION = "reduced_motion"
    LABELS = "labels"


class SEOKind(str, Enum):
    """An SEO requirement a section must satisfy."""

    HEADING_HIERARCHY = "heading_hierarchy"
    STRUCTURED_DATA = "structured_data"
    META = "meta"
    CANONICAL = "canonical"
    INTERNAL_LINK = "internal_link"
    IMAGE_ALT = "image_alt"
    CRAWLABILITY = "crawlability"
    SEMANTIC_MARKUP = "semantic_markup"


class PerformanceKind(str, Enum):
    """A performance consideration a section must honour."""

    LAZY_LOAD = "lazy_load"
    IMAGE_OPTIMIZATION = "image_optimization"
    CRITICAL_CSS = "critical_css"
    DEFER_SCRIPT = "defer_script"
    PRELOAD = "preload"
    CODE_SPLIT = "code_split"
    CACHE = "cache"
    MINIMIZE_LAYOUT_SHIFT = "minimize_layout_shift"


class IOKind(str, Enum):
    """The kind of artifact that flows into or out of a section (execution wiring)."""

    DATA = "data"
    ASSET = "asset"
    STATE = "state"
    EVENT = "event"
    ARTIFACT = "artifact"


# --------------------------------------------------------------------------- #
# Approval                                                                     #
# --------------------------------------------------------------------------- #
class ApprovalGate(str, Enum):
    """The rigor of the gate a section/page must pass before it is built in Figma."""

    AUTO = "auto"
    DESIGN_REVIEW = "design_review"
    DESIGN_DIRECTOR = "design_director"
    STRATEGY_SIGNOFF = "strategy_signoff"


class ApproverRole(str, Enum):
    """Who signs off at a gate."""

    SYSTEM = "system"
    DESIGNER = "designer"
    DESIGN_DIRECTOR = "design_director"
    STRATEGIST = "strategist"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the six wireframe-planning graphs."""

    WIREFRAME = "wireframe"
    SECTION_DEPENDENCY = "section_dependency"
    CONTENT = "content"
    COMPONENT = "component"
    EXECUTION = "execution"
    APPROVAL = "approval"


class NodeKind(str, Enum):
    """The kind of node a wireframe-graph node represents."""

    PAGE = "page"
    SECTION = "section"
    BLOCK = "block"
    COMPONENT = "component"
    DATA = "data"
    ASSET = "asset"
    APPROVAL_GATE = "approval_gate"


class GraphRelation(str, Enum):
    """A typed, directed edge between two wireframe-graph nodes.

    ``CONTAINS``, ``ORDERED_BEFORE``, ``DEPENDS_ON``, ``REQUIRES``, ``COMPOSES`` and
    ``GATES`` must be acyclic — a cyclic build/approval plan is not executable. ``PRODUCES``
    and ``CONSUMES`` wire sections to the data/assets that flow between them.
    """

    CONTAINS = "contains"
    ORDERED_BEFORE = "ordered_before"
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    COMPOSES = "composes"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    GATES = "gates"


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
            raise InvalidWireframeValueError(
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
            raise InvalidWireframeValueError(
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
class WFScore:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidWireframeValueError(
                "WFScore.value must be within [0, 100].", details={"value": self.value}
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
        raise InvalidWireframeValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidWireframeValueError(
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
            raise InvalidWireframeValueError(
                "Rank must be an int >= 1.", details={"value": self.value}
            )

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A runner-up option the planner weighed and rejected — the trade-off record.

    A principal product designer does not just state a plan; they show what else fit the
    evidence and why it lost. Recording the considered alternative keeps every planning
    decision honest and auditable.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidWireframeValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidWireframeValueError(
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
            raise InvalidWireframeValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
