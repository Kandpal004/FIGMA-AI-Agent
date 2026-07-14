"""Page specs — the deterministic per-page-type IA knowledge base.

Each :class:`PageType` maps to a :class:`PageSpec`: the requirement, purpose, goals, the
required and optional sections (with placement, priority, and content blocks), the primary
and secondary actions, the per-dimension priorities, and the trust/conversion placement of a
world-class ecommerce page of that kind. This is the explainable knowledge the rule-based
architect reasons from — a codification of Shopify / Adobe Commerce IA practice by page, not
a random generator.

Pure data: standard library and the shared value objects only.
"""

from __future__ import annotations

from dataclasses import dataclass

from ia.domain.shared.value_objects import (
    ContentBlockKind,
    PageRequirement,
    PageType,
    Placement,
    SectionType,
)

__all__ = ["PageSpec", "SectionSpec", "spec_for"]


@dataclass(frozen=True, slots=True)
class SectionSpec:
    """A section within a page spec."""

    type: SectionType
    placement: Placement
    priority: int
    required: bool
    blocks: tuple[tuple[ContentBlockKind, str], ...] = ()


@dataclass(frozen=True, slots=True)
class PageSpec:
    """The IA register a page type expresses."""

    requirement: PageRequirement
    purpose: str
    slug: str
    business_goal: str
    primary_user_goal: str
    secondary_user_goal: str
    sections: tuple[SectionSpec, ...]
    primary_action: tuple[str, PageType | None] | None
    secondary_actions: tuple[str, ...]
    # (navigation, seo, accessibility, conversion, mobile)
    priorities: tuple[int, int, int, int, int]
    trust_placement: Placement
    conversion_placement: Placement


_R = PageRequirement.REQUIRED
_O = PageRequirement.OPTIONAL
_CB = ContentBlockKind

_SPECS: dict[PageType, PageSpec] = {
    PageType.HOMEPAGE: PageSpec(
        _R, "Orient the visitor and route them to the right path.", "/",
        "Establish credibility and drive entry into the funnel.",
        "Find a credible starting point quickly.", "Understand what the brand offers.",
        (
            SectionSpec(SectionType.GLOBAL_NAV, Placement.HEADER, 5, True, ((_CB.LINK, "primary nav"),)),
            SectionSpec(SectionType.HERO, Placement.ABOVE_FOLD, 5, True, ((_CB.HEADING, "value headline"), (_CB.CTA, "shop"))),
            SectionSpec(SectionType.VALUE_PROP, Placement.ABOVE_FOLD, 4, True, ((_CB.BODY, "value points"),)),
            SectionSpec(SectionType.CATEGORY_GRID, Placement.MID, 4, True, ((_CB.LINK, "collections"),)),
            SectionSpec(SectionType.FEATURED_PRODUCTS, Placement.MID, 3, False, ((_CB.PRODUCT_CARD, "featured"),)),
            SectionSpec(SectionType.SOCIAL_PROOF, Placement.BELOW_FOLD, 3, True, ((_CB.REVIEW_ITEM, "proof"),)),
            SectionSpec(SectionType.FOOTER, Placement.FOOTER, 4, True, ((_CB.LINK, "footer links"),)),
        ),
        ("explore products", PageType.COLLECTION), ("search",),
        (5, 5, 4, 4, 4), Placement.BELOW_FOLD, Placement.ABOVE_FOLD,
    ),
    PageType.COLLECTION: PageSpec(
        _R, "Help the shopper narrow to relevant products.", "/collections/:handle",
        "Turn broad intent into a shortlist.", "Filter to relevant products.", "Compare options.",
        (
            SectionSpec(SectionType.BREADCRUMBS, Placement.HEADER, 4, True, ((_CB.LINK, "trail"),)),
            SectionSpec(SectionType.FILTERS, Placement.ABOVE_FOLD, 5, True, ((_CB.LIST, "facets"),)),
            SectionSpec(SectionType.SORT_BAR, Placement.ABOVE_FOLD, 4, True, ((_CB.LIST, "sort options"),)),
            SectionSpec(SectionType.RESULTS_GRID, Placement.MID, 5, True, ((_CB.PRODUCT_CARD, "products"),)),
            SectionSpec(SectionType.RELATED_PRODUCTS, Placement.BELOW_FOLD, 2, False, ((_CB.PRODUCT_CARD, "related"),)),
        ),
        ("view product", PageType.PRODUCT), ("filter", "sort"),
        (5, 5, 4, 4, 4), Placement.MID, Placement.MID,
    ),
    PageType.PRODUCT: PageSpec(
        _R, "Give the shopper confidence to add to cart.", "/products/:handle",
        "Convert consideration into add-to-cart.", "Decide this product is right.", "Trust the purchase.",
        (
            SectionSpec(SectionType.BREADCRUMBS, Placement.HEADER, 3, True, ((_CB.LINK, "trail"),)),
            SectionSpec(SectionType.PRODUCT_GALLERY, Placement.ABOVE_FOLD, 5, True, ((_CB.IMAGE, "gallery"),)),
            SectionSpec(SectionType.BUY_BOX, Placement.ABOVE_FOLD, 5, True, ((_CB.PRICE, "price"), (_CB.CTA, "add to cart"))),
            SectionSpec(SectionType.VARIANT_SELECTOR, Placement.ABOVE_FOLD, 4, True, ((_CB.FORM_FIELD, "variants"),)),
            SectionSpec(SectionType.PRODUCT_INFO, Placement.MID, 4, True, ((_CB.BODY, "description"),)),
            SectionSpec(SectionType.TRUST_BADGES, Placement.ABOVE_FOLD, 4, True, ((_CB.BADGE, "guarantee"),)),
            SectionSpec(SectionType.REVIEWS, Placement.BELOW_FOLD, 4, True, ((_CB.REVIEW_ITEM, "reviews"),)),
            SectionSpec(SectionType.SPECIFICATIONS, Placement.BELOW_FOLD, 3, False, ((_CB.LIST, "specs"),)),
            SectionSpec(SectionType.CROSS_SELL, Placement.BELOW_FOLD, 3, False, ((_CB.PRODUCT_CARD, "cross-sell"),)),
            SectionSpec(SectionType.RELATED_PRODUCTS, Placement.BELOW_FOLD, 3, False, ((_CB.PRODUCT_CARD, "related"),)),
        ),
        ("add to cart", PageType.CART), ("read reviews", "add to wishlist"),
        (4, 5, 5, 5, 5), Placement.ABOVE_FOLD, Placement.ABOVE_FOLD,
    ),
    PageType.CART: PageSpec(
        _R, "Reassure and move the shopper to checkout.", "/cart",
        "Start checkout with intent intact.", "Confirm the order and proceed.", "Adjust quantities.",
        (
            SectionSpec(SectionType.CART_LINE_ITEMS, Placement.ABOVE_FOLD, 5, True, ((_CB.PRODUCT_CARD, "items"),)),
            SectionSpec(SectionType.CART_SUMMARY, Placement.ABOVE_FOLD, 5, True, ((_CB.PRICE, "totals"), (_CB.CTA, "checkout"))),
            SectionSpec(SectionType.TRUST_BADGES, Placement.MID, 4, True, ((_CB.BADGE, "secure"),)),
            SectionSpec(SectionType.CROSS_SELL, Placement.BELOW_FOLD, 3, False, ((_CB.PRODUCT_CARD, "add-ons"),)),
        ),
        ("start checkout", PageType.CHECKOUT), ("continue shopping",),
        (4, 3, 5, 5, 5), Placement.MID, Placement.ABOVE_FOLD,
    ),
    PageType.CHECKOUT: PageSpec(
        _R, "Complete the purchase with least effort and most trust.", "/checkout",
        "Convert intent into a completed order.", "Pay quickly and safely.", "Feel the purchase is secure.",
        (
            SectionSpec(SectionType.CHECKOUT_FORM, Placement.ABOVE_FOLD, 5, True, ((_CB.FORM_FIELD, "contact/shipping"),)),
            SectionSpec(SectionType.SHIPPING, Placement.MID, 4, True, ((_CB.FORM_FIELD, "shipping options"),)),
            SectionSpec(SectionType.PAYMENT, Placement.MID, 5, True, ((_CB.FORM_FIELD, "payment"),)),
            SectionSpec(SectionType.ORDER_SUMMARY, Placement.STICKY, 5, True, ((_CB.PRICE, "summary"), (_CB.CTA, "pay"))),
            SectionSpec(SectionType.TRUST_BADGES, Placement.MID, 4, True, ((_CB.BADGE, "secure checkout"),)),
        ),
        ("complete purchase", None), ("edit cart",),
        (2, 2, 5, 5, 5), Placement.MID, Placement.STICKY,
    ),
    PageType.SEARCH: PageSpec(
        _R, "Return relevant results fast and recover from no-results.", "/search",
        "Serve high-intent shoppers.", "Find the right product quickly.", "Refine the query.",
        (
            SectionSpec(SectionType.SEARCH_BAR, Placement.HEADER, 5, True, ((_CB.FORM_FIELD, "query"),)),
            SectionSpec(SectionType.FILTERS, Placement.ABOVE_FOLD, 4, True, ((_CB.LIST, "facets"),)),
            SectionSpec(SectionType.SORT_BAR, Placement.ABOVE_FOLD, 3, True, ((_CB.LIST, "sort"),)),
            SectionSpec(SectionType.RESULTS_GRID, Placement.MID, 5, True, ((_CB.PRODUCT_CARD, "results"),)),
        ),
        ("view product", PageType.PRODUCT), ("refine search",),
        (3, 4, 4, 4, 4), Placement.MID, Placement.MID,
    ),
    PageType.ACCOUNT: PageSpec(
        _R, "Let returning customers manage orders and details.", "/account",
        "Support retention with easy self-service.", "Manage my orders.", "Update my details.",
        (
            SectionSpec(SectionType.ACCOUNT_MENU, Placement.ABOVE_FOLD, 4, True, ((_CB.LINK, "menu"),)),
            SectionSpec(SectionType.ORDER_HISTORY, Placement.MID, 5, True, ((_CB.LIST, "orders"),)),
        ),
        ("view orders", None), ("edit profile",),
        (3, 2, 5, 3, 4), Placement.MID, Placement.MID,
    ),
    PageType.WISHLIST: PageSpec(
        _O, "Let shoppers save products for later.", "/wishlist",
        "Recover intent and drive return visits.", "Save products to consider.", "Move saved items to cart.",
        (
            SectionSpec(SectionType.RESULTS_GRID, Placement.ABOVE_FOLD, 4, True, ((_CB.PRODUCT_CARD, "saved items"),)),
        ),
        ("add to cart", PageType.CART), ("remove",),
        (2, 2, 4, 4, 4), Placement.MID, Placement.ABOVE_FOLD,
    ),
    PageType.BLOG: PageSpec(
        _O, "Build authority and support SEO and consideration.", "/blog",
        "Drive organic traffic and trust.", "Learn and get inspired.", "Discover related products.",
        (
            SectionSpec(SectionType.ARTICLE_LIST, Placement.MID, 4, True, ((_CB.LINK, "articles"),)),
            SectionSpec(SectionType.RELATED_PRODUCTS, Placement.BELOW_FOLD, 2, False, ((_CB.PRODUCT_CARD, "shop the post"),)),
        ),
        ("read article", None), ("subscribe",),
        (3, 5, 4, 2, 4), Placement.BELOW_FOLD, Placement.BELOW_FOLD,
    ),
    PageType.LANDING: PageSpec(
        _O, "Convert a targeted visitor on one focused message.", "/pages/:handle",
        "Match a campaign promise and drive one action.", "Act on a specific offer.", "Understand the offer.",
        (
            SectionSpec(SectionType.HERO, Placement.ABOVE_FOLD, 5, True, ((_CB.HEADING, "offer"), (_CB.CTA, "shop"))),
            SectionSpec(SectionType.VALUE_PROP, Placement.MID, 4, True, ((_CB.BODY, "benefits"),)),
            SectionSpec(SectionType.SOCIAL_PROOF, Placement.MID, 3, True, ((_CB.REVIEW_ITEM, "proof"),)),
        ),
        ("shop now", PageType.COLLECTION), ("learn more",),
        (2, 4, 4, 5, 5), Placement.MID, Placement.ABOVE_FOLD,
    ),
    PageType.ABOUT: PageSpec(
        _O, "Tell the brand story and build trust.", "/pages/about",
        "Deepen brand trust and affinity.", "Understand who the brand is.", "Decide to trust the brand.",
        (
            SectionSpec(SectionType.CONTENT_BLOCK, Placement.MID, 4, True, ((_CB.BODY, "story"),)),
            SectionSpec(SectionType.SOCIAL_PROOF, Placement.BELOW_FOLD, 3, False, ((_CB.REVIEW_ITEM, "press"),)),
        ),
        ("shop the brand", PageType.COLLECTION), ("contact",),
        (2, 4, 4, 2, 4), Placement.MID, Placement.BELOW_FOLD,
    ),
    PageType.CONTACT: PageSpec(
        _O, "Let customers reach support easily.", "/pages/contact",
        "Reduce support friction and build trust.", "Get help quickly.", "Find answers first.",
        (
            SectionSpec(SectionType.CONTACT_FORM, Placement.ABOVE_FOLD, 4, True, ((_CB.FORM_FIELD, "message"),)),
            SectionSpec(SectionType.FAQ, Placement.MID, 3, False, ((_CB.LIST, "faqs"),)),
        ),
        ("send message", None), ("view faq",),
        (2, 3, 5, 2, 4), Placement.MID, Placement.MID,
    ),
    PageType.CUSTOM_CMS: PageSpec(
        _O, "Serve a bespoke content need.", "/pages/:handle",
        "Support a specific content or campaign goal.", "Get the content they came for.", "",
        (
            SectionSpec(SectionType.CONTENT_BLOCK, Placement.MID, 3, True, ((_CB.BODY, "content"),)),
        ),
        None, (),
        (2, 3, 4, 2, 4), Placement.BELOW_FOLD, Placement.MID,
    ),
}


def spec_for(page: PageType) -> PageSpec:
    """Return the IA spec for a page type."""
    return _SPECS[page]
