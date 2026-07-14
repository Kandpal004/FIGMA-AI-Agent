"""Shared value objects for the Information Architecture Engine.

These immutable, self-validating value objects are the vocabulary the engine reasons in:
the provenance of the evidence it cites, the page and section types it structures, the
navigation and relationship kinds it wires, the product-discovery primitives it defines,
the kinds of graph it builds, and the calibrated scales it scores everything on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, no global mutable state, and no import of any
provider or other engine — those are reached only through ports, keeping this domain
independent.

Testing considerations
----------------------
* :class:`PageType` has exactly thirteen members (the required page taxonomy) and
  :class:`GraphKind` exactly six.
* :class:`Confidence`, :class:`IAScore`, :class:`Percentage`, and :class:`Priority`
  validate their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "ActionType",
    "Confidence",
    "ConsideredAlternative",
    "ContentBlockKind",
    "DiscoveryKind",
    "FilterType",
    "GraphKind",
    "GraphRelation",
    "IAScore",
    "InvalidIAValueError",
    "NavKind",
    "NodeKind",
    "PageRequirement",
    "PageType",
    "Percentage",
    "Placement",
    "Priority",
    "PriorityDimension",
    "ProvenanceKind",
    "QualityBand",
    "Rank",
    "RelationshipKind",
    "SectionType",
    "SortOption",
    "Tag",
]


class InvalidIAValueError(DesignDirectorError):
    """Raised when an IA value object is constructed with invalid data."""

    code = "invalid_ia_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The upstream strategy/experience engines and the platform engines today; future
    structural-analytics sources (search analytics, heatmaps, GA4) extend this additively.
    """

    UX_STRATEGY = "ux_strategy"
    PSYCHOLOGY = "psychology"
    BRAND_STRATEGY = "brand_strategy"
    BUSINESS_STRATEGY = "business_strategy"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    REASONING = "reasoning"
    ANALYTICS = "analytics"
    SEARCH_ANALYTICS = "search_analytics"
    HEATMAP = "heatmap"
    GA4 = "ga4"


# --------------------------------------------------------------------------- #
# Pages & sections                                                             #
# --------------------------------------------------------------------------- #
class PageType(str, Enum):
    """One of the thirteen supported page types."""

    HOMEPAGE = "homepage"
    COLLECTION = "collection"
    PRODUCT = "product"
    CART = "cart"
    CHECKOUT = "checkout"
    SEARCH = "search"
    BLOG = "blog"
    LANDING = "landing"
    ACCOUNT = "account"
    WISHLIST = "wishlist"
    ABOUT = "about"
    CONTACT = "contact"
    CUSTOM_CMS = "custom_cms"


class PageRequirement(str, Enum):
    """Whether a page is required for the experience or optional."""

    REQUIRED = "required"
    OPTIONAL = "optional"


class SectionType(str, Enum):
    """A structural section a page can contain (ecommerce taxonomy)."""

    HERO = "hero"
    VALUE_PROP = "value_prop"
    FEATURED_PRODUCTS = "featured_products"
    CATEGORY_GRID = "category_grid"
    PRODUCT_GALLERY = "product_gallery"
    PRODUCT_INFO = "product_info"
    BUY_BOX = "buy_box"
    VARIANT_SELECTOR = "variant_selector"
    PRICING = "pricing"
    REVIEWS = "reviews"
    RATINGS_SUMMARY = "ratings_summary"
    TRUST_BADGES = "trust_badges"
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
    CART_SUMMARY = "cart_summary"
    CART_LINE_ITEMS = "cart_line_items"
    CHECKOUT_FORM = "checkout_form"
    ORDER_SUMMARY = "order_summary"
    PAYMENT = "payment"
    SHIPPING = "shipping"
    NEWSLETTER = "newsletter"
    CONTENT_BLOCK = "content_block"
    BREADCRUMBS = "breadcrumbs"
    GLOBAL_NAV = "global_nav"
    FOOTER = "footer"
    ACCOUNT_MENU = "account_menu"
    ORDER_HISTORY = "order_history"
    CONTACT_FORM = "contact_form"
    ARTICLE_LIST = "article_list"
    ARTICLE_BODY = "article_body"


class ContentBlockKind(str, Enum):
    """The atomic content unit within a section (the leaves of the content tree)."""

    HEADING = "heading"
    BODY = "body"
    IMAGE = "image"
    CTA = "cta"
    LIST = "list"
    FORM_FIELD = "form_field"
    PRODUCT_CARD = "product_card"
    REVIEW_ITEM = "review_item"
    BADGE = "badge"
    PRICE = "price"
    MEDIA = "media"
    LINK = "link"


class ActionType(str, Enum):
    """The prominence tier of a page action."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class Placement(str, Enum):
    """Where a section/element sits within a page's vertical structure."""

    HEADER = "header"
    ABOVE_FOLD = "above_fold"
    MID = "mid"
    BELOW_FOLD = "below_fold"
    FOOTER = "footer"
    STICKY = "sticky"


# --------------------------------------------------------------------------- #
# Navigation, relationships, discovery                                         #
# --------------------------------------------------------------------------- #
class NavKind(str, Enum):
    """A navigation surface."""

    GLOBAL = "global"
    MEGA_MENU = "mega_menu"
    FOOTER = "footer"
    BREADCRUMBS = "breadcrumbs"
    UTILITY = "utility"


class RelationshipKind(str, Enum):
    """A typed relationship between two pages."""

    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"
    RELATED = "related"
    RECOMMENDED = "recommended"
    INTERNAL_LINK = "internal_link"
    PARENT_CHILD = "parent_child"
    SEQUENCE = "sequence"


class DiscoveryKind(str, Enum):
    """A product-discovery mechanism."""

    SEARCH = "search"
    FILTER = "filter"
    SORT = "sort"


class FilterType(str, Enum):
    """A faceted-navigation filter type."""

    CATEGORY = "category"
    PRICE = "price"
    BRAND = "brand"
    RATING = "rating"
    ATTRIBUTE = "attribute"
    AVAILABILITY = "availability"
    COLOR = "color"
    SIZE = "size"


class SortOption(str, Enum):
    """A sort option for results."""

    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"
    BESTSELLING = "bestselling"
    RATING = "rating"


class PriorityDimension(str, Enum):
    """A dimension a page is prioritised along."""

    NAVIGATION = "navigation"
    SEO = "seo"
    ACCESSIBILITY = "accessibility"
    CONVERSION = "conversion"
    MOBILE = "mobile"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the six IA graphs."""

    SITEMAP = "sitemap"
    NAVIGATION = "navigation"
    PAGE = "page"
    SECTION = "section"
    RELATIONSHIP = "relationship"
    CONTENT_TREE = "content_tree"


class NodeKind(str, Enum):
    """The kind of node an IA-graph node represents."""

    PAGE = "page"
    SECTION = "section"
    CONTENT = "content"
    NAV_ITEM = "nav_item"
    ACTION = "action"
    CONTENT_BLOCK = "content_block"


class GraphRelation(str, Enum):
    """A typed, directed edge between two IA-graph nodes.

    ``CONTAINS``, ``LEADS_TO``, ``PRECEDES`` and ``DERIVES_FROM`` must be acyclic.
    ``LINKS_TO`` and ``RELATES_TO`` may be mutual.
    """

    CONTAINS = "contains"
    LINKS_TO = "links_to"
    LEADS_TO = "leads_to"
    RELATES_TO = "relates_to"
    DERIVES_FROM = "derives_from"
    PRECEDES = "precedes"
    CROSS_SELLS = "cross_sells"
    UPSELLS = "upsells"


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
            raise InvalidIAValueError(
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
            raise InvalidIAValueError(
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
class IAScore:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidIAValueError(
                "IAScore.value must be within [0, 100].", details={"value": self.value}
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
        raise InvalidIAValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidIAValueError(
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
            raise InvalidIAValueError("Rank must be an int >= 1.", details={"value": self.value})

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A runner-up option the engine weighed and rejected — the trade-off record.

    A principal information architect does not just state a structure; they show what else
    fit the evidence and why it lost. Recording the considered alternative keeps every
    decision honest and auditable.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidIAValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidIAValueError(
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
            raise InvalidIAValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
