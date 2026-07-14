"""Page specs — the deterministic per-page UX knowledge base.

Each :class:`PageKind` maps to a :class:`PageSpec`: the objective, the primary and
secondary CTAs, the success metrics, the content priority, and the UX laws that most
govern a world-class ecommerce page of that kind. This is the explainable knowledge the
rule-based strategist reasons from — a codification of NN/g / Baymard / Shopify UX
practice by page, not a random generator.

Pure data: standard library and the shared value objects only.
"""

from __future__ import annotations

from dataclasses import dataclass

from ux.domain.shared.value_objects import (
    ContentType,
    MetricKind,
    PageKind,
    UXLaw,
)

__all__ = ["PageSpec", "spec_for"]


@dataclass(frozen=True, slots=True)
class PageSpec:
    """The UX register a page kind expresses."""

    objective: str
    why_it_exists: str
    primary_action: str
    primary_target: PageKind | None
    secondary_action: str
    metrics: tuple[MetricKind, ...]
    content: tuple[ContentType, ...]
    laws: tuple[UXLaw, ...]


_SPECS: dict[PageKind, PageSpec] = {
    PageKind.HOME: PageSpec(
        objective="Orient the visitor and route them to the right path quickly.",
        why_it_exists="To establish credibility and hand the visitor off to the path that matches their intent.",
        primary_action="explore products", primary_target=PageKind.CATEGORY,
        secondary_action="search",
        metrics=(MetricKind.ENGAGEMENT, MetricKind.BOUNCE_RATE),
        content=(ContentType.VALUE_PROPOSITION, ContentType.NAVIGATION, ContentType.SOCIAL_PROOF),
        laws=(UXLaw.JAKOBS, UXLaw.HICKS, UXLaw.GESTALT),
    ),
    PageKind.CATEGORY: PageSpec(
        objective="Help the shopper narrow to relevant products with confidence.",
        why_it_exists="To turn broad intent into a shortlist through effective filtering and scanning.",
        primary_action="view product", primary_target=PageKind.PRODUCT,
        secondary_action="filter and sort",
        metrics=(MetricKind.ADD_TO_CART_RATE, MetricKind.ENGAGEMENT),
        content=(ContentType.PRODUCT_INFO, ContentType.NAVIGATION, ContentType.PRICING),
        laws=(UXLaw.MILLERS, UXLaw.GESTALT, UXLaw.BAYMARD),
    ),
    PageKind.PRODUCT: PageSpec(
        objective="Give the shopper the confidence to add to cart.",
        why_it_exists="To answer every question and objection so the shopper can commit.",
        primary_action="add to cart", primary_target=PageKind.CART,
        secondary_action="read reviews",
        metrics=(MetricKind.ADD_TO_CART_RATE, MetricKind.CONVERSION_RATE),
        content=(ContentType.PRODUCT_INFO, ContentType.SOCIAL_PROOF, ContentType.TRUST_SIGNAL,
                 ContentType.PRICING, ContentType.CTA),
        laws=(UXLaw.PROGRESSIVE_DISCLOSURE, UXLaw.MILLERS, UXLaw.GESTALT, UXLaw.BAYMARD),
    ),
    PageKind.SEARCH: PageSpec(
        objective="Return relevant results fast and recover gracefully from no-results.",
        why_it_exists="To serve high-intent shoppers who already know what they want.",
        primary_action="view product", primary_target=PageKind.PRODUCT,
        secondary_action="refine search",
        metrics=(MetricKind.ENGAGEMENT, MetricKind.ADD_TO_CART_RATE),
        content=(ContentType.PRODUCT_INFO, ContentType.NAVIGATION),
        laws=(UXLaw.NIELSEN_HEURISTICS, UXLaw.BAYMARD, UXLaw.OCCAMS),
    ),
    PageKind.CART: PageSpec(
        objective="Reassure the shopper and move them to checkout without doubt.",
        why_it_exists="To confirm the choice, remove hesitation, and start checkout.",
        primary_action="start checkout", primary_target=PageKind.CHECKOUT,
        secondary_action="continue shopping",
        metrics=(MetricKind.CHECKOUT_COMPLETION, MetricKind.AOV),
        content=(ContentType.PRODUCT_INFO, ContentType.PRICING, ContentType.TRUST_SIGNAL, ContentType.CTA),
        laws=(UXLaw.BAYMARD, UXLaw.NIELSEN_HEURISTICS, UXLaw.HICKS),
    ),
    PageKind.CHECKOUT: PageSpec(
        objective="Complete the purchase with the least effort and the most trust.",
        why_it_exists="To convert intent into an order while protecting against last-minute drop-off.",
        primary_action="complete purchase", primary_target=PageKind.POST_PURCHASE,
        secondary_action="edit cart",
        metrics=(MetricKind.CHECKOUT_COMPLETION, MetricKind.CONVERSION_RATE),
        content=(ContentType.PRICING, ContentType.TRUST_SIGNAL, ContentType.SUPPORT, ContentType.POLICY, ContentType.CTA),
        laws=(UXLaw.TESLERS, UXLaw.BAYMARD, UXLaw.NIELSEN_HEURISTICS, UXLaw.WCAG, UXLaw.HICKS),
    ),
    PageKind.ACCOUNT: PageSpec(
        objective="Let returning customers manage orders and details effortlessly.",
        why_it_exists="To support retention by making self-service simple.",
        primary_action="manage orders", primary_target=None,
        secondary_action="update details",
        metrics=(MetricKind.RETURN_RATE, MetricKind.ENGAGEMENT),
        content=(ContentType.SUPPORT, ContentType.NAVIGATION, ContentType.POLICY),
        laws=(UXLaw.NIELSEN_HEURISTICS, UXLaw.OCCAMS, UXLaw.WCAG),
    ),
    PageKind.POST_PURCHASE: PageSpec(
        objective="Affirm the good decision and open the door to return.",
        why_it_exists="To reduce post-purchase anxiety and seed loyalty and advocacy.",
        primary_action="track order", primary_target=None,
        secondary_action="create account",
        metrics=(MetricKind.RETURN_RATE, MetricKind.ENGAGEMENT),
        content=(ContentType.TRUST_SIGNAL, ContentType.SUPPORT, ContentType.SOCIAL_PROOF),
        laws=(UXLaw.NIELSEN_HEURISTICS, UXLaw.GESTALT),
    ),
    PageKind.LANDING: PageSpec(
        objective="Convert a targeted visitor on a single, focused message.",
        why_it_exists="To match a campaign's promise and drive one clear action.",
        primary_action="shop now", primary_target=PageKind.CATEGORY,
        secondary_action="learn more",
        metrics=(MetricKind.CONVERSION_RATE, MetricKind.BOUNCE_RATE),
        content=(ContentType.VALUE_PROPOSITION, ContentType.SOCIAL_PROOF, ContentType.CTA),
        laws=(UXLaw.OCCAMS, UXLaw.HICKS, UXLaw.FITTS),
    ),
}


def spec_for(page: PageKind) -> PageSpec:
    """Return the UX spec for a page kind."""
    return _SPECS[page]
