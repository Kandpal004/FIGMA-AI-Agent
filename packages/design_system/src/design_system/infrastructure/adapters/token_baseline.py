"""The codified token baseline — the raw design intelligence the architect works from.

This module holds the platform's canonical, three-tier token blueprint for an enterprise
commerce storefront: the primitive palette/scales, the semantic roles that reference them, the
component-scoped tokens, the scale/system relationships, the ten state definitions, the light and
dark theme remappings, and the per-component blueprints (atomic level, tokens, properties,
variants, states, responsive behaviour, accessibility, performance). It is deliberately *data*,
not domain objects — the :class:`RuleBasedTokenArchitect` turns these blueprints into cited
domain tokens/specs, adapting them to the brief and grounding each in the gathered evidence.

Nothing here is fake or placeholder: these are real, defensible defaults (a 4px spacing grid, a
1.25 modular type scale, WCAG-AA contrast, mobile-first responsive behaviour) that a principal
design-systems architect would ship and then tune per brand.

Pure data + the shared value-object enums; no domain aggregates, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from design_system.domain.shared.value_objects import (
    AtomicLevel,
    Breakpoint,
    ComponentType,
    PropertyType,
    StateKind,
    TokenCategory,
    TokenTier,
)

__all__ = [
    "BASELINE",
    "ComponentBlueprint",
    "PropertyBlueprint",
    "StateBlueprint",
    "TokenBaseline",
    "TokenBlueprint",
    "VariantBlueprint",
]

_C = TokenCategory


@dataclass(frozen=True, slots=True)
class TokenBlueprint:
    """A single token before it is grounded: key, category, tier, and literal-or-ref value."""

    key: str
    category: TokenCategory
    tier: TokenTier
    literal: str | None = None
    ref: str | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class PropertyBlueprint:
    """A component property blueprint."""

    name: str
    type: PropertyType
    options: tuple[str, ...] = ()
    default: str | None = None
    required: bool = False


@dataclass(frozen=True, slots=True)
class VariantBlueprint:
    """A component variant blueprint."""

    name: str
    property_values: dict[str, str]
    description: str = ""


@dataclass(frozen=True, slots=True)
class StateBlueprint:
    """A component state blueprint (which state, and the token slots it activates)."""

    state: StateKind
    token_refs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ComponentBlueprint:
    """A component blueprint before it is grounded into a cited spec."""

    component: ComponentType
    atomic_level: AtomicLevel
    token_refs: tuple[str, ...]
    properties: tuple[PropertyBlueprint, ...]
    variants: tuple[VariantBlueprint, ...]
    states: tuple[StateKind, ...]
    responsive: dict[Breakpoint, str]
    role: str
    keyboard: tuple[str, ...]
    min_contrast: float = 4.5
    lazy_load: bool = False
    blocks_lcp: bool = False


@dataclass(frozen=True, slots=True)
class TokenBaseline:
    """The complete codified baseline."""

    tokens: tuple[TokenBlueprint, ...]
    typography_base_px: float
    typography_ratio: float
    typography_roles: tuple[str, ...]
    spacing_base_px: float
    spacing_steps: tuple[str, ...]
    radius_steps: tuple[str, ...]
    elevation_levels: tuple[str, ...]
    shadow_steps: tuple[str, ...]
    border_widths: tuple[str, ...]
    breakpoints: dict[Breakpoint, int]
    grid_columns: dict[Breakpoint, int]
    grid_gutters: dict[Breakpoint, str]
    container_widths: dict[Breakpoint, int]
    motion_durations: tuple[str, ...]
    motion_easings: tuple[str, ...]
    focus_ring_token: str
    hit_target_token: str
    transition_token: str
    states: tuple[StateBlueprint, ...]
    light_theme: dict[str, str]
    dark_theme: dict[str, str]
    rtl_mirror_properties: tuple[str, ...]
    components: tuple[ComponentBlueprint, ...]


# --------------------------------------------------------------------------- #
# Primitives                                                                   #
# --------------------------------------------------------------------------- #
def _prim(key: str, category: TokenCategory, literal: str, desc: str = "") -> TokenBlueprint:
    return TokenBlueprint(key, category, TokenTier.PRIMITIVE, literal=literal, description=desc)


def _sem(key: str, category: TokenCategory, ref: str, desc: str = "") -> TokenBlueprint:
    return TokenBlueprint(key, category, TokenTier.SEMANTIC, ref=ref, description=desc)


def _comp(key: str, category: TokenCategory, ref: str, desc: str = "") -> TokenBlueprint:
    return TokenBlueprint(key, category, TokenTier.COMPONENT, ref=ref, description=desc)


_PRIMITIVES: tuple[TokenBlueprint, ...] = (
    # Neutral palette (0 = white … 900 = near-black).
    _prim("gray.0", _C.COLOR, "#FFFFFF"),
    _prim("gray.50", _C.COLOR, "#F7F7F8"),
    _prim("gray.100", _C.COLOR, "#EDEDF0"),
    _prim("gray.200", _C.COLOR, "#D9D9DE"),
    _prim("gray.300", _C.COLOR, "#B8B8C0"),
    _prim("gray.400", _C.COLOR, "#8A8A94"),
    _prim("gray.500", _C.COLOR, "#6B6B75"),
    _prim("gray.600", _C.COLOR, "#4D4D55"),
    _prim("gray.700", _C.COLOR, "#333339"),
    _prim("gray.800", _C.COLOR, "#1C1C21"),
    _prim("gray.900", _C.COLOR, "#0A0A0C"),
    # Brand + feedback.
    _prim("brand.500", _C.COLOR, "#2B59FF"),
    _prim("brand.600", _C.COLOR, "#1E42CC"),
    _prim("accent.500", _C.COLOR, "#FF5C35"),
    _prim("success.500", _C.COLOR, "#1F9D55"),
    _prim("warning.500", _C.COLOR, "#C77700"),
    _prim("error.500", _C.COLOR, "#D22D2D"),
    # Type sizes (px).
    _prim("type.size.100", _C.TYPOGRAPHY, "12px"),
    _prim("type.size.200", _C.TYPOGRAPHY, "14px"),
    _prim("type.size.300", _C.TYPOGRAPHY, "16px"),
    _prim("type.size.400", _C.TYPOGRAPHY, "20px"),
    _prim("type.size.500", _C.TYPOGRAPHY, "24px"),
    _prim("type.size.600", _C.TYPOGRAPHY, "32px"),
    _prim("type.size.700", _C.TYPOGRAPHY, "40px"),
    # Spacing (4px grid).
    _prim("space.0", _C.SPACING, "0"),
    _prim("space.1", _C.SPACING, "4px"),
    _prim("space.2", _C.SPACING, "8px"),
    _prim("space.3", _C.SPACING, "12px"),
    _prim("space.4", _C.SPACING, "16px"),
    _prim("space.5", _C.SPACING, "20px"),
    _prim("space.6", _C.SPACING, "24px"),
    _prim("space.8", _C.SPACING, "32px"),
    _prim("space.10", _C.SPACING, "40px"),
    _prim("space.12", _C.SPACING, "48px"),
    _prim("space.16", _C.SPACING, "64px"),
    # Radius.
    _prim("radius.none", _C.RADIUS, "0"),
    _prim("radius.sm", _C.RADIUS, "4px"),
    _prim("radius.md", _C.RADIUS, "8px"),
    _prim("radius.lg", _C.RADIUS, "16px"),
    _prim("radius.full", _C.RADIUS, "9999px"),
    # Shadow.
    _prim("shadow.sm", _C.SHADOW, "0 1px 2px rgba(10,10,12,0.08)"),
    _prim("shadow.md", _C.SHADOW, "0 4px 12px rgba(10,10,12,0.12)"),
    _prim("shadow.lg", _C.SHADOW, "0 12px 32px rgba(10,10,12,0.18)"),
    # Elevation (surface levels).
    _prim("elevation.0", _C.ELEVATION, "0"),
    _prim("elevation.1", _C.ELEVATION, "1"),
    _prim("elevation.2", _C.ELEVATION, "2"),
    _prim("elevation.3", _C.ELEVATION, "3"),
    # Border widths.
    _prim("border.0", _C.BORDER, "0"),
    _prim("border.1", _C.BORDER, "1px"),
    _prim("border.2", _C.BORDER, "2px"),
    # Motion.
    _prim("motion.duration.fast", _C.MOTION, "120ms"),
    _prim("motion.duration.base", _C.MOTION, "200ms"),
    _prim("motion.duration.slow", _C.MOTION, "320ms"),
    _prim("motion.ease.standard", _C.MOTION, "cubic-bezier(0.2,0,0,1)"),
    _prim("motion.ease.emphasized", _C.MOTION, "cubic-bezier(0.3,0,0,1)"),
    _prim("motion.ease.decelerate", _C.MOTION, "cubic-bezier(0,0,0,1)"),
    # Interaction primitives.
    _prim("interaction.focus-ring", _C.INTERACTION, "0 0 0 3px rgba(43,89,255,0.45)"),
    _prim("interaction.hit-target", _C.INTERACTION, "44px"),
    # Opacity + z-index.
    _prim("opacity.disabled", _C.OPACITY, "0.4"),
    _prim("opacity.muted", _C.OPACITY, "0.64"),
    _prim("z.dropdown", _C.Z_INDEX, "1000"),
    _prim("z.overlay", _C.Z_INDEX, "1100"),
    _prim("z.modal", _C.Z_INDEX, "1200"),
)

# --------------------------------------------------------------------------- #
# Semantic roles                                                               #
# --------------------------------------------------------------------------- #
_SEMANTICS: tuple[TokenBlueprint, ...] = (
    _sem("color.text.default", _C.COLOR, "gray.900"),
    _sem("color.text.muted", _C.COLOR, "gray.600"),
    _sem("color.text.inverse", _C.COLOR, "gray.0"),
    _sem("color.bg.default", _C.COLOR, "gray.0"),
    _sem("color.bg.subtle", _C.COLOR, "gray.50"),
    _sem("color.bg.inverse", _C.COLOR, "gray.900"),
    _sem("color.action.primary", _C.COLOR, "brand.500"),
    _sem("color.action.primary.hover", _C.COLOR, "brand.600"),
    _sem("color.border.default", _C.COLOR, "gray.200"),
    _sem("color.border.strong", _C.COLOR, "gray.400"),
    _sem("color.feedback.success", _C.COLOR, "success.500"),
    _sem("color.feedback.warning", _C.COLOR, "warning.500"),
    _sem("color.feedback.error", _C.COLOR, "error.500"),
    _sem("type.caption", _C.TYPOGRAPHY, "type.size.100"),
    _sem("type.body", _C.TYPOGRAPHY, "type.size.300"),
    _sem("type.h3", _C.TYPOGRAPHY, "type.size.500"),
    _sem("type.h2", _C.TYPOGRAPHY, "type.size.600"),
    _sem("type.h1", _C.TYPOGRAPHY, "type.size.700"),
    _sem("interaction.transition", _C.INTERACTION, "motion.duration.base"),
)

# --------------------------------------------------------------------------- #
# Component-scoped tokens                                                       #
# --------------------------------------------------------------------------- #
_COMPONENT_TOKENS: tuple[TokenBlueprint, ...] = (
    _comp("button.bg.default", _C.COLOR, "color.action.primary"),
    _comp("button.bg.hover", _C.COLOR, "color.action.primary.hover"),
    _comp("button.text", _C.COLOR, "color.text.inverse"),
    _comp("button.radius", _C.RADIUS, "radius.md"),
    _comp("card.bg", _C.COLOR, "color.bg.default"),
    _comp("card.radius", _C.RADIUS, "radius.lg"),
    _comp("card.shadow", _C.SHADOW, "shadow.sm"),
    _comp("input.bg", _C.COLOR, "color.bg.default"),
    _comp("input.border", _C.COLOR, "color.border.default"),
    _comp("input.radius", _C.RADIUS, "radius.sm"),
    _comp("surface.bg", _C.COLOR, "color.bg.default"),
    _comp("surface.border", _C.COLOR, "color.border.default"),
)

# --------------------------------------------------------------------------- #
# States                                                                        #
# --------------------------------------------------------------------------- #
_STATES: tuple[StateBlueprint, ...] = (
    StateBlueprint(StateKind.DEFAULT, {}),
    StateBlueprint(StateKind.HOVER, {"bg": "button.bg.hover"}),
    StateBlueprint(StateKind.FOCUS, {"ring": "interaction.focus-ring"}),
    StateBlueprint(StateKind.ACTIVE, {"bg": "color.action.primary.hover"}),
    StateBlueprint(StateKind.DISABLED, {"opacity": "opacity.disabled"}),
    StateBlueprint(StateKind.LOADING, {"fg": "color.text.muted"}),
    StateBlueprint(StateKind.EMPTY, {"fg": "color.text.muted"}),
    StateBlueprint(StateKind.ERROR, {"fg": "color.feedback.error"}),
    StateBlueprint(StateKind.SUCCESS, {"fg": "color.feedback.success"}),
    StateBlueprint(StateKind.WARNING, {"fg": "color.feedback.warning"}),
)

# --------------------------------------------------------------------------- #
# Themes (must theme the SAME semantic keys for parity)                         #
# --------------------------------------------------------------------------- #
_LIGHT_THEME: dict[str, str] = {
    "color.text.default": "gray.900",
    "color.text.muted": "gray.600",
    "color.bg.default": "gray.0",
    "color.bg.subtle": "gray.50",
    "color.border.default": "gray.200",
}
_DARK_THEME: dict[str, str] = {
    "color.text.default": "gray.50",
    "color.text.muted": "gray.400",
    "color.bg.default": "gray.900",
    "color.bg.subtle": "gray.800",
    "color.border.default": "gray.700",
}

# --------------------------------------------------------------------------- #
# Component blueprints                                                          #
# --------------------------------------------------------------------------- #
_ALL_STATES = (
    StateKind.DEFAULT,
    StateKind.HOVER,
    StateKind.FOCUS,
    StateKind.ACTIVE,
    StateKind.DISABLED,
)
_LIST_STATES = (StateKind.DEFAULT, StateKind.LOADING, StateKind.EMPTY)


def _resp(mobile: str, desktop: str) -> dict[Breakpoint, str]:
    return {Breakpoint.MOBILE: mobile, Breakpoint.DESKTOP: desktop}


_COMPONENTS: tuple[ComponentBlueprint, ...] = (
    ComponentBlueprint(
        ComponentType.HEADER, AtomicLevel.ORGANISM,
        ("surface.bg", "surface.border", "space.4", "color.text.default"),
        (PropertyBlueprint("sticky", PropertyType.BOOLEAN, default=None),),
        (VariantBlueprint("sticky", {"sticky": "true"}, "Pinned on scroll"),),
        (StateKind.DEFAULT, StateKind.FOCUS),
        _resp("collapsed with menu toggle", "full horizontal nav"),
        "banner", ("tab",), blocks_lcp=True,
    ),
    ComponentBlueprint(
        ComponentType.NAVIGATION, AtomicLevel.MOLECULE,
        ("color.text.default", "color.action.primary", "space.4", "interaction.focus-ring"),
        (PropertyBlueprint("orientation", PropertyType.VARIANT,
                           ("horizontal", "vertical"), "horizontal"),),
        (VariantBlueprint("horizontal", {"orientation": "horizontal"}),
         VariantBlueprint("vertical", {"orientation": "vertical"})),
        _ALL_STATES, _resp("drawer", "inline"),
        "navigation", ("tab", "enter", "escape"),
    ),
    ComponentBlueprint(
        ComponentType.HERO, AtomicLevel.ORGANISM,
        ("color.bg.inverse", "color.text.inverse", "type.h1", "space.12"),
        (PropertyBlueprint("layout", PropertyType.VARIANT,
                           ("full-bleed", "split"), "full-bleed"),),
        (VariantBlueprint("full-bleed", {"layout": "full-bleed"}),
         VariantBlueprint("split", {"layout": "split"})),
        (StateKind.DEFAULT,), _resp("stacked, single column", "two column"),
        "region", ("tab",), blocks_lcp=True,
    ),
    ComponentBlueprint(
        ComponentType.PRODUCT_CARD, AtomicLevel.MOLECULE,
        ("card.bg", "card.radius", "card.shadow", "type.body", "space.3"),
        (PropertyBlueprint("size", PropertyType.VARIANT, ("compact", "regular"), "regular"),
         PropertyBlueprint("show_quick_add", PropertyType.BOOLEAN)),
        (VariantBlueprint("compact", {"size": "compact"}),
         VariantBlueprint("regular", {"size": "regular"})),
        _ALL_STATES, _resp("full-width tile", "grid tile"),
        "group", ("tab", "enter"), lazy_load=True,
    ),
    ComponentBlueprint(
        ComponentType.PRODUCT_GRID, AtomicLevel.ORGANISM,
        ("space.4", "color.bg.default", "surface.border"),
        (PropertyBlueprint("columns", PropertyType.NUMBER),),
        (VariantBlueprint("dense", {"columns": "4"}, "4-up on desktop"),),
        _LIST_STATES, _resp("1 column", "3–4 columns"),
        "list", ("tab",), lazy_load=True,
    ),
    ComponentBlueprint(
        ComponentType.PRODUCT_INFORMATION, AtomicLevel.ORGANISM,
        ("type.h1", "type.body", "color.text.default", "space.6"),
        (PropertyBlueprint("layout", PropertyType.VARIANT, ("stacked", "columns"), "columns"),),
        (VariantBlueprint("stacked", {"layout": "stacked"}),
         VariantBlueprint("columns", {"layout": "columns"})),
        (StateKind.DEFAULT, StateKind.LOADING), _resp("stacked", "gallery + info columns"),
        "region", ("tab",), blocks_lcp=True,
    ),
    ComponentBlueprint(
        ComponentType.VARIANT_PICKER, AtomicLevel.MOLECULE,
        ("input.border", "input.radius", "color.action.primary", "space.2"),
        (PropertyBlueprint("style", PropertyType.VARIANT, ("swatch", "dropdown"), "swatch"),),
        (VariantBlueprint("swatch", {"style": "swatch"}),
         VariantBlueprint("dropdown", {"style": "dropdown"})),
        _ALL_STATES, _resp("wrap", "inline"),
        "radiogroup", ("tab", "arrowright", "arrowleft", "enter"),
    ),
    ComponentBlueprint(
        ComponentType.STICKY_ADD_TO_CART, AtomicLevel.MOLECULE,
        ("button.bg.default", "button.text", "button.radius", "shadow.lg", "space.4"),
        (PropertyBlueprint("visible_on", PropertyType.VARIANT,
                           ("scroll", "always"), "scroll"),),
        (VariantBlueprint("scroll", {"visible_on": "scroll"}),),
        _ALL_STATES, _resp("fixed bottom bar", "inline in info column"),
        "complementary", ("tab", "enter"),
    ),
    ComponentBlueprint(
        ComponentType.CART_DRAWER, AtomicLevel.ORGANISM,
        ("surface.bg", "surface.border", "shadow.lg", "z.overlay", "space.4"),
        (PropertyBlueprint("side", PropertyType.VARIANT, ("right", "left"), "right"),),
        (VariantBlueprint("right", {"side": "right"}),
         VariantBlueprint("left", {"side": "left"})),
        (StateKind.DEFAULT, StateKind.LOADING, StateKind.EMPTY, StateKind.FOCUS),
        _resp("full-screen sheet", "side drawer"),
        "dialog", ("tab", "escape"),
    ),
    ComponentBlueprint(
        ComponentType.FORMS, AtomicLevel.MOLECULE,
        ("input.bg", "input.border", "input.radius", "color.feedback.error", "space.3"),
        (PropertyBlueprint("state", PropertyType.VARIANT,
                           ("default", "error", "success"), "default"),),
        (VariantBlueprint("error", {"state": "error"}),
         VariantBlueprint("success", {"state": "success"})),
        (StateKind.DEFAULT, StateKind.FOCUS, StateKind.DISABLED,
         StateKind.ERROR, StateKind.SUCCESS),
        _resp("full-width fields", "grid fields"),
        "form", ("tab", "enter"),
    ),
    ComponentBlueprint(
        ComponentType.SEARCH, AtomicLevel.MOLECULE,
        ("input.bg", "input.border", "input.radius", "color.text.muted", "space.3"),
        (PropertyBlueprint("mode", PropertyType.VARIANT,
                           ("inline", "overlay"), "inline"),),
        (VariantBlueprint("inline", {"mode": "inline"}),
         VariantBlueprint("overlay", {"mode": "overlay"})),
        (StateKind.DEFAULT, StateKind.FOCUS, StateKind.LOADING, StateKind.EMPTY),
        _resp("icon opens overlay", "inline field"),
        "search", ("tab", "enter", "escape"),
    ),
    ComponentBlueprint(
        ComponentType.FILTERS, AtomicLevel.ORGANISM,
        ("surface.bg", "surface.border", "color.action.primary", "space.4"),
        (PropertyBlueprint("layout", PropertyType.VARIANT, ("sidebar", "drawer"), "sidebar"),),
        (VariantBlueprint("sidebar", {"layout": "sidebar"}),
         VariantBlueprint("drawer", {"layout": "drawer"})),
        (StateKind.DEFAULT, StateKind.FOCUS, StateKind.EMPTY),
        _resp("bottom-sheet drawer", "left sidebar"),
        "group", ("tab", "enter", "escape"),
    ),
    ComponentBlueprint(
        ComponentType.BREADCRUMBS, AtomicLevel.MOLECULE,
        ("type.caption", "color.text.muted", "color.action.primary", "space.2"),
        (PropertyBlueprint("collapse", PropertyType.BOOLEAN),),
        (VariantBlueprint("collapsed", {"collapse": "true"}, "Middle crumbs collapse"),),
        (StateKind.DEFAULT, StateKind.HOVER, StateKind.FOCUS),
        _resp("truncated", "full trail"),
        "navigation", ("tab",),
    ),
    ComponentBlueprint(
        ComponentType.FOOTER, AtomicLevel.ORGANISM,
        ("color.bg.subtle", "color.text.muted", "type.caption", "space.8"),
        (PropertyBlueprint("columns", PropertyType.NUMBER),),
        (VariantBlueprint("multi-column", {"columns": "4"}),),
        (StateKind.DEFAULT, StateKind.FOCUS),
        _resp("stacked accordions", "multi-column"),
        "contentinfo", ("tab",), lazy_load=True,
    ),
)


BASELINE = TokenBaseline(
    tokens=_PRIMITIVES + _SEMANTICS + _COMPONENT_TOKENS,
    typography_base_px=16.0,
    typography_ratio=1.25,
    typography_roles=("type.caption", "type.body", "type.h3", "type.h2", "type.h1"),
    spacing_base_px=4.0,
    spacing_steps=("space.1", "space.2", "space.3", "space.4", "space.6", "space.8"),
    radius_steps=("radius.none", "radius.sm", "radius.md", "radius.lg", "radius.full"),
    elevation_levels=("elevation.0", "elevation.1", "elevation.2", "elevation.3"),
    shadow_steps=("shadow.sm", "shadow.md", "shadow.lg"),
    border_widths=("border.0", "border.1", "border.2"),
    breakpoints={
        Breakpoint.MOBILE: 0,
        Breakpoint.TABLET: 768,
        Breakpoint.DESKTOP: 1024,
        Breakpoint.WIDE: 1440,
    },
    grid_columns={
        Breakpoint.MOBILE: 4,
        Breakpoint.TABLET: 8,
        Breakpoint.DESKTOP: 12,
        Breakpoint.WIDE: 12,
    },
    grid_gutters={
        Breakpoint.MOBILE: "space.4",
        Breakpoint.TABLET: "space.4",
        Breakpoint.DESKTOP: "space.6",
        Breakpoint.WIDE: "space.6",
    },
    container_widths={
        Breakpoint.MOBILE: 640,
        Breakpoint.TABLET: 768,
        Breakpoint.DESKTOP: 1200,
        Breakpoint.WIDE: 1440,
    },
    motion_durations=("motion.duration.fast", "motion.duration.base", "motion.duration.slow"),
    motion_easings=("motion.ease.standard", "motion.ease.emphasized", "motion.ease.decelerate"),
    focus_ring_token="interaction.focus-ring",
    hit_target_token="interaction.hit-target",
    transition_token="interaction.transition",
    states=_STATES,
    light_theme=_LIGHT_THEME,
    dark_theme=_DARK_THEME,
    rtl_mirror_properties=(
        "padding-inline-start",
        "padding-inline-end",
        "margin-inline-start",
        "text-align",
        "float",
    ),
    components=_COMPONENTS,
)
