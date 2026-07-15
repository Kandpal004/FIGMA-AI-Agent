"""The codified orchestration rulebook — the deterministic ordering/binding intelligence.

This module holds the platform's canonical, per-page section blueprint for an enterprise commerce
storefront: for each page type, the ordered sections and, for each, the role, the component and
variant, the layout/spacing/typography/visual choices, the responsive/animation/accessibility/
performance directives, and the trade-off considered. It is deliberately *data*, not domain
objects — the :class:`RuleBasedExecutionPlanner` turns these blueprints into cited domain section
plans, adapting them to the brief and grounding each in the gathered evidence.

Every token key here is a real Design System (P16) token key (``color.bg.default``, ``space.4``,
``type.h1``, ``motion.duration.base``, …), so the bindings the orchestrator emits resolve against
the design system — the "no guessing" guarantee starts in this rulebook. The ordering reflects
real conversion sequencing (above-the-fold hero, trust before the fold, reviews and related
products deferred), not convention.

Pure data + the shared value-object enums; no domain aggregates, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from design_orchestrator.domain.shared.value_objects import (
    Alignment,
    ComponentType,
    Density,
    LayoutMode,
    PageType,
    SectionRole,
    ThemeMode,
)

__all__ = ["PAGE_BLUEPRINTS", "SectionBlueprint"]

_C = ComponentType
_R = SectionRole


@dataclass(frozen=True, slots=True)
class SectionBlueprint:
    """One section before it is grounded into a cited plan."""

    role: SectionRole
    component: ComponentType
    variant: str
    layout_mode: LayoutMode
    heading_token: str
    body_token: str
    gap_token: str
    block_token: str
    surface_tokens: tuple[str, ...]
    emphasis: int
    theme_mode: ThemeMode = ThemeMode.LIGHT
    alignment: Alignment = Alignment.START
    density: Density = Density.REGULAR
    columns: int = 1
    duration_token: str = "motion.duration.base"
    easing_token: str = "motion.ease.standard"
    trigger: str = "on-scroll"
    responsive: dict = field(default_factory=dict)
    a11y_role: str = "region"
    keyboard: tuple[str, ...] = ("tab",)
    min_contrast: float = 4.5
    lazy_load: bool = False
    priority: int = 3
    blocks_lcp: bool = False
    alternative: tuple[str, str] | None = None


def _resp(mobile: str, desktop: str) -> dict:
    from design_orchestrator.domain.shared.value_objects import Breakpoint

    return {Breakpoint.MOBILE: mobile, Breakpoint.DESKTOP: desktop}


def _header() -> SectionBlueprint:
    return SectionBlueprint(
        _R.HEADER, _C.HEADER, "sticky", LayoutMode.STACK,
        "type.h3", "type.body", "space.4", "space.4", ("color.bg.default",), 1,
        a11y_role="banner", responsive=_resp("collapsed menu", "full nav"),
        priority=5, duration_token="motion.duration.fast",
    )


def _footer() -> SectionBlueprint:
    return SectionBlueprint(
        _R.FOOTER, _C.FOOTER, "multi-column", LayoutMode.GRID,
        "type.h3", "type.caption", "space.6", "space.12", ("color.bg.subtle",), 1,
        columns=4, a11y_role="contentinfo", responsive=_resp("stacked", "multi-column"),
        lazy_load=True, priority=2,
    )


PAGE_BLUEPRINTS: dict[PageType, tuple[SectionBlueprint, ...]] = {
    PageType.HOMEPAGE: (
        _header(),
        SectionBlueprint(
            _R.HERO, _C.HERO, "full-bleed", LayoutMode.FULL_BLEED,
            "type.h1", "type.body", "space.8", "space.16", ("color.bg.inverse",), 3,
            theme_mode=ThemeMode.DARK, alignment=Alignment.CENTER, density=Density.SPACIOUS,
            trigger="on-load", responsive=_resp("stacked", "two column"),
            priority=5, blocks_lcp=True,
            alternative=("hero_carousel", "A single hero converts better than a rotating carousel"),
        ),
        SectionBlueprint(
            _R.TRUST, _C.USP_GRID, "regular", LayoutMode.GRID,
            "type.h3", "type.body", "space.6", "space.12", ("color.bg.default",), 2,
            columns=3, responsive=_resp("stacked", "three column"),
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.CATEGORY_GRID, "regular", LayoutMode.GRID,
            "type.h2", "type.body", "space.6", "space.12", ("color.bg.default",), 2,
            columns=3, responsive=_resp("two column", "three column"),
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.PRODUCT_GRID, "dense", LayoutMode.GRID,
            "type.h2", "type.body", "space.4", "space.12", ("color.bg.subtle",), 2,
            columns=4, a11y_role="list", responsive=_resp("one column", "four column"),
            lazy_load=True, priority=2,
        ),
        SectionBlueprint(
            _R.TRUST, _C.TESTIMONIALS, "regular", LayoutMode.STACK,
            "type.h2", "type.body", "space.6", "space.12", ("color.bg.default",), 2,
            responsive=_resp("stacked", "carousel"), lazy_load=True, priority=2,
        ),
        SectionBlueprint(
            _R.CONVERSION, _C.NEWSLETTER, "inline", LayoutMode.SPLIT,
            "type.h3", "type.body", "space.4", "space.12", ("color.bg.inverse",), 2,
            theme_mode=ThemeMode.DARK, a11y_role="form", keyboard=("tab", "enter"),
            responsive=_resp("stacked", "split"), lazy_load=True, priority=2,
        ),
        _footer(),
    ),
    PageType.COLLECTION: (
        _header(),
        SectionBlueprint(
            _R.NAVIGATION, _C.BREADCRUMBS, "collapsed", LayoutMode.STACK,
            "type.caption", "type.caption", "space.4", "space.4", ("color.bg.default",), 1,
            a11y_role="navigation", responsive=_resp("truncated", "full trail"), priority=4,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.FILTERS, "sidebar", LayoutMode.SPLIT,
            "type.h3", "type.body", "space.4", "space.8", ("color.bg.subtle",), 1,
            keyboard=("tab", "enter", "escape"), responsive=_resp("bottom-sheet", "left sidebar"),
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.SORTING, "default", LayoutMode.STACK,
            "type.body", "type.caption", "space.4", "space.4", ("color.bg.default",), 1,
            keyboard=("tab", "enter"), responsive=_resp("dropdown", "inline"), priority=4,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.PRODUCT_GRID, "dense", LayoutMode.GRID,
            "type.h2", "type.body", "space.4", "space.8", ("color.bg.default",), 2,
            columns=4, a11y_role="list", responsive=_resp("one column", "four column"),
            lazy_load=True, priority=3,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.PAGINATION, "default", LayoutMode.STACK,
            "type.body", "type.caption", "space.4", "space.8", ("color.bg.default",), 1,
            a11y_role="navigation", keyboard=("tab", "enter"),
            responsive=_resp("compact", "numbered"), lazy_load=True, priority=2,
        ),
        _footer(),
    ),
    PageType.PRODUCT: (
        _header(),
        SectionBlueprint(
            _R.NAVIGATION, _C.BREADCRUMBS, "collapsed", LayoutMode.STACK,
            "type.caption", "type.caption", "space.4", "space.4", ("color.bg.default",), 1,
            a11y_role="navigation", responsive=_resp("truncated", "full trail"), priority=4,
        ),
        SectionBlueprint(
            _R.CONTENT, _C.PRODUCT_GALLERY, "regular", LayoutMode.SPLIT,
            "type.h2", "type.body", "space.4", "space.8", ("color.bg.default",), 3,
            responsive=_resp("stacked gallery", "gallery column"), priority=5, blocks_lcp=True,
        ),
        SectionBlueprint(
            _R.CONTENT, _C.PRODUCT_INFORMATION, "columns", LayoutMode.SPLIT,
            "type.h1", "type.body", "space.6", "space.8", ("color.bg.default",), 3,
            responsive=_resp("stacked", "info column"), priority=5,
        ),
        SectionBlueprint(
            _R.CONVERSION, _C.VARIANT_PICKER, "swatch", LayoutMode.STACK,
            "type.h3", "type.body", "space.4", "space.6", ("color.bg.default",), 2,
            a11y_role="radiogroup", keyboard=("tab", "arrowright", "arrowleft", "enter"),
            responsive=_resp("wrap", "inline"), priority=5,
        ),
        SectionBlueprint(
            _R.CONVERSION, _C.STICKY_ADD_TO_CART, "scroll", LayoutMode.STACK,
            "type.h3", "type.body", "space.4", "space.4", ("color.action.primary",), 3,
            a11y_role="complementary", keyboard=("tab", "enter"),
            responsive=_resp("fixed bottom bar", "inline"), priority=5,
        ),
        SectionBlueprint(
            _R.TRUST, _C.TRUST_BADGES, "regular", LayoutMode.GRID,
            "type.caption", "type.caption", "space.4", "space.8", ("color.bg.subtle",), 1,
            columns=3, responsive=_resp("wrap", "row"), priority=3,
        ),
        SectionBlueprint(
            _R.TRUST, _C.REVIEWS, "regular", LayoutMode.STACK,
            "type.h2", "type.body", "space.6", "space.12", ("color.bg.default",), 2,
            responsive=_resp("stacked", "two column"), lazy_load=True, priority=2,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.RELATED_PRODUCTS, "regular", LayoutMode.GRID,
            "type.h2", "type.body", "space.4", "space.12", ("color.bg.subtle",), 2,
            columns=4, a11y_role="list", responsive=_resp("carousel", "four column"),
            lazy_load=True, priority=2,
        ),
        _footer(),
    ),
    PageType.CART: (
        _header(),
        SectionBlueprint(
            _R.FORM, _C.FORMS, "default", LayoutMode.SPLIT,
            "type.h1", "type.body", "space.6", "space.8", ("color.bg.default",), 3,
            a11y_role="form", keyboard=("tab", "enter"),
            responsive=_resp("stacked", "summary aside"), priority=5,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.RECOMMENDATIONS, "regular", LayoutMode.GRID,
            "type.h2", "type.body", "space.4", "space.12", ("color.bg.subtle",), 2,
            columns=4, a11y_role="list", responsive=_resp("carousel", "four column"),
            lazy_load=True, priority=2,
        ),
        SectionBlueprint(
            _R.TRUST, _C.TRUST_BADGES, "regular", LayoutMode.GRID,
            "type.caption", "type.caption", "space.4", "space.8", ("color.bg.subtle",), 1,
            columns=3, responsive=_resp("wrap", "row"), priority=3,
        ),
        _footer(),
    ),
    PageType.CHECKOUT: (
        _header(),
        SectionBlueprint(
            _R.CONVERSION, _C.CHECKOUT_BLOCKS, "default", LayoutMode.SPLIT,
            "type.h1", "type.body", "space.6", "space.8", ("color.bg.default",), 3,
            a11y_role="form", keyboard=("tab", "enter"),
            responsive=_resp("stacked", "form + summary"), priority=5, blocks_lcp=True,
        ),
        SectionBlueprint(
            _R.TRUST, _C.TRUST_BADGES, "regular", LayoutMode.GRID,
            "type.caption", "type.caption", "space.4", "space.8", ("color.bg.subtle",), 1,
            columns=3, responsive=_resp("wrap", "row"), priority=4,
        ),
        _footer(),
    ),
    PageType.SEARCH: (
        _header(),
        SectionBlueprint(
            _R.DISCOVERY, _C.SEARCH, "inline", LayoutMode.STACK,
            "type.h2", "type.body", "space.4", "space.8", ("color.bg.default",), 2,
            a11y_role="search", keyboard=("tab", "enter", "escape"),
            responsive=_resp("overlay", "inline"), priority=5,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.FILTERS, "drawer", LayoutMode.SPLIT,
            "type.h3", "type.body", "space.4", "space.8", ("color.bg.subtle",), 1,
            keyboard=("tab", "enter", "escape"), responsive=_resp("bottom-sheet", "left sidebar"),
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.PRODUCT_GRID, "dense", LayoutMode.GRID,
            "type.h2", "type.body", "space.4", "space.8", ("color.bg.default",), 2,
            columns=4, a11y_role="list", responsive=_resp("one column", "four column"),
            lazy_load=True, priority=3,
        ),
        SectionBlueprint(
            _R.DISCOVERY, _C.PAGINATION, "default", LayoutMode.STACK,
            "type.body", "type.caption", "space.4", "space.8", ("color.bg.default",), 1,
            a11y_role="navigation", keyboard=("tab", "enter"),
            responsive=_resp("compact", "numbered"), lazy_load=True, priority=2,
        ),
        _footer(),
    ),
    PageType.ACCOUNT: (
        _header(),
        SectionBlueprint(
            _R.CONTENT, _C.ACCOUNT, "default", LayoutMode.SPLIT,
            "type.h1", "type.body", "space.6", "space.8", ("color.bg.default",), 2,
            a11y_role="region", keyboard=("tab", "enter"),
            responsive=_resp("stacked", "nav + panel"), priority=4,
        ),
        SectionBlueprint(
            _R.CONTENT, _C.ORDER_TIMELINE, "default", LayoutMode.STACK,
            "type.h2", "type.body", "space.4", "space.8", ("color.bg.subtle",), 1,
            responsive=_resp("stacked", "timeline"), lazy_load=True, priority=2,
        ),
        _footer(),
    ),
}
