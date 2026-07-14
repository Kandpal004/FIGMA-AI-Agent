"""The codified review standards — what a 25-year Creative Director checks per dimension.

For each of the sixteen review dimensions this encodes: the evidence keywords and upstream
provenances that *should* be present for the dimension to pass, the design anti-pattern that
their absence represents, whether the dimension is critical (its absence blocks approval), and
the concern and fix wording. The rule-based panel is a thin, testable mapping over this — the
judgement of a premium-ecommerce Creative Director expressed as data, not a prompt.

Pure data over the shared value objects. No I/O, no framework.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.domain.shared.value_objects import (
    AntiPattern,
    ProvenanceKind,
    ReviewDimension,
)

__all__ = ["DIMENSION_STANDARDS", "DimensionStandard", "standard_for"]

_P = ProvenanceKind
_D = ReviewDimension
_A = AntiPattern


@dataclass(frozen=True, slots=True)
class DimensionStandard:
    """What one dimension is judged against."""

    dimension: ReviewDimension
    keywords: tuple[str, ...]
    expected: tuple[ProvenanceKind, ...]
    anti_pattern: AntiPattern | None
    critical: bool
    concern: str
    fix: str


_STANDARDS: tuple[DimensionStandard, ...] = (
    DimensionStandard(
        _D.BUSINESS_ALIGNMENT, ("business", "positioning", "conversion", "revenue", "aov"),
        (_P.BUSINESS_STRATEGY, _P.WIREFRAME), _A.GENERIC_AI_PATTERN, True,
        "Every section must advance a stated business goal; a design without business purpose "
        "reads as a generic AI/Dribbble layout.",
        "Tie each section to a business goal grounded in the business strategy.",
    ),
    DimensionStandard(
        _D.BRAND_ALIGNMENT, ("brand", "tone", "positioning", "voice"),
        (_P.BRAND_STRATEGY,), _A.GENERIC_AI_PATTERN, False,
        "The plan must express the brand's positioning and tone, not a generic template.",
        "Carry the brand tone and positioning into content and emphasis.",
    ),
    DimensionStandard(
        _D.PSYCHOLOGY_ALIGNMENT, ("trust", "objection", "anxiety", "emotion", "confidence"),
        (_P.PSYCHOLOGY,), _A.LOW_TRUST, False,
        "Section placement must answer the customer's objections and anxieties.",
        "Address the psychology's objections and trust needs at the point of decision.",
    ),
    DimensionStandard(
        _D.UX_QUALITY, ("ux", "goal", "navigation", "flow", "user"),
        (_P.UX_STRATEGY, _P.WIREFRAME), _A.GENERIC_LAYOUT, True,
        "The plan must execute a coherent UX strategy, not a stock hero-features-footer layout.",
        "Ground page and section order in the UX strategy's goals and flow.",
    ),
    DimensionStandard(
        _D.INFORMATION_HIERARCHY, ("hierarchy", "priority", "structure", "section", "order"),
        (_P.INFORMATION_ARCHITECTURE, _P.WIREFRAME), _A.WEAK_HIERARCHY, True,
        "Sections must have a clear, differentiated priority order; undifferentiated sections "
        "signal a weak hierarchy.",
        "Establish a clear priority order grounded in the information architecture.",
    ),
    DimensionStandard(
        _D.CONVERSION_STRATEGY, ("conversion", "cta", "checkout", "buy", "cart"),
        (_P.WIREFRAME, _P.UX_STRATEGY, _P.BUSINESS_STRATEGY), _A.POOR_CRO, True,
        "The plan must drive conversion with a clear primary action; missing CTAs are poor CRO.",
        "Give every conversion page a dominant, grounded primary call to action.",
    ),
    DimensionStandard(
        _D.TRUST_SIGNALS, ("trust", "review", "guarantee", "badge", "social"),
        (_P.WIREFRAME, _P.PSYCHOLOGY), _A.LOW_TRUST, True,
        "Trust signals must appear where decisions are made (PDP, cart, checkout); their "
        "absence is low trust.",
        "Place reviews, guarantees, and security signals at the point of decision.",
    ),
    DimensionStandard(
        _D.TYPOGRAPHY_DIRECTION, ("typography", "tone", "brand", "heading", "hierarchy"),
        (_P.BRAND_STRATEGY,), _A.WEAK_TYPOGRAPHY, False,
        "A typographic direction must derive from the brand; a default type treatment reads "
        "generic.",
        "Derive a typographic direction from the brand voice and hierarchy.",
    ),
    DimensionStandard(
        _D.SPACING_LOGIC, ("spacing", "layout", "structure", "hierarchy", "rhythm"),
        (_P.INFORMATION_ARCHITECTURE, _P.KNOWLEDGE), _A.POOR_SPACING, False,
        "Spacing must follow the content hierarchy; even spacing everywhere flattens meaning.",
        "Apply a spacing logic that reinforces the section priority order.",
    ),
    DimensionStandard(
        _D.ACCESSIBILITY, ("accessibility", "wcag", "contrast", "keyboard", "aria", "alt"),
        (_P.WIREFRAME, _P.KNOWLEDGE), None, False,
        "The plan must carry accessibility requirements (keyboard, contrast, labels).",
        "Attach WCAG-aligned accessibility requirements to every section.",
    ),
    DimensionStandard(
        _D.PERFORMANCE_IMPACT, ("performance", "lazy", "image", "speed", "layout-shift"),
        (_P.WIREFRAME, _P.KNOWLEDGE), None, False,
        "The plan must honour a performance budget (lazy-loading, image optimisation).",
        "Attach performance considerations to media-heavy sections.",
    ),
    DimensionStandard(
        _D.MOBILE_EXPERIENCE, ("mobile", "responsive", "touch", "stack", "reflow"),
        (_P.WIREFRAME, _P.UX_STRATEGY), None, False,
        "The plan must define responsive behaviour for mobile-first commerce.",
        "Specify per-breakpoint responsive behaviour for every section.",
    ),
    DimensionStandard(
        _D.DEVELOPER_FEASIBILITY, ("component", "feasibility", "structure", "pattern"),
        (_P.WIREFRAME, _P.KNOWLEDGE), None, False,
        "Components must be standard and buildable, not bespoke one-offs.",
        "Prefer standard, composable components with clear data contracts.",
    ),
    DimensionStandard(
        _D.SHOPIFY_COMPATIBILITY, ("shopify", "theme", "section", "component", "platform"),
        (_P.WIREFRAME, _P.KNOWLEDGE), None, False,
        "The plan must map to Shopify sections and theme conventions.",
        "Align sections and components with Shopify theme building blocks.",
    ),
    DimensionStandard(
        _D.MAGENTO_COMPATIBILITY, ("magento", "adobe", "theme", "component", "platform"),
        (_P.WIREFRAME, _P.KNOWLEDGE), None, False,
        "The plan must map to Adobe Commerce (Magento) blocks and theme conventions.",
        "Align sections and components with Adobe Commerce building blocks.",
    ),
    DimensionStandard(
        _D.FUTURE_SCALABILITY, ("scalability", "maintainability", "component", "consistency", "reuse"),
        (_P.WIREFRAME, _P.KNOWLEDGE), None, False,
        "The plan must reuse consistent components so it scales and stays maintainable.",
        "Consolidate on a consistent, reusable component set.",
    ),
)

DIMENSION_STANDARDS: dict[ReviewDimension, DimensionStandard] = {
    s.dimension: s for s in _STANDARDS
}


def standard_for(dimension: ReviewDimension) -> DimensionStandard:
    """Return the review standard for a dimension."""
    return DIMENSION_STANDARDS[dimension]
