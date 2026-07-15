"""The codified file-structure rulebook — how a senior designer builds a Figma file.

This module holds the platform's canonical structure for an enterprise storefront Figma file: the
variable collections and their modes (a Theme collection with Light/Dark, a Primitive collection
of raw scales, a Device collection with Desktop/Tablet/Mobile), the published styles, the
component sets and their variants, and the page organization (a Cover, a Design System page, a
Components page, and one page per storefront page with its ordered section instances). It is
deliberately *data*, not domain objects — the :class:`RuleBasedFigmaComposer` turns these specs
into cited domain pages, variables, styles, and component sets.

Every token key here is a real Design-System variable key, so bindings resolve; the file
organization reflects how professional teams actually structure Figma files. Nothing here imports
a Figma SDK, MCP client, or HTTP library.

Pure data + the shared value-object enums.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from figma_design.domain.shared.value_objects import (
    CollectionKind,
    ComponentPropertyType,
    StyleType,
    VariableScope,
    VariableType,
)

__all__ = [
    "COLLECTIONS",
    "COMPONENT_SETS",
    "ComponentSetSpec",
    "PageSectionSpec",
    "STOREFRONT_PAGES",
    "StorefrontPageSpec",
    "STYLES",
    "StyleSpec",
    "VariableSpec",
    "CollectionSpec",
]


@dataclass(frozen=True, slots=True)
class VariableSpec:
    """A variable before it is grounded: key, type, scopes, and a value per mode."""

    key: str
    type: VariableType
    scopes: tuple[VariableScope, ...]
    # mode -> ("lit", value) | ("ref", variable_key)
    values: dict[str, tuple[str, str]]


@dataclass(frozen=True, slots=True)
class CollectionSpec:
    """A variable collection before it is grounded."""

    kind: CollectionKind
    name: str
    modes: tuple[str, ...]
    variables: tuple[VariableSpec, ...]


@dataclass(frozen=True, slots=True)
class StyleSpec:
    """A published style before it is grounded."""

    name: str
    type: StyleType
    color_token: str = ""
    font_family: str = "Inter"
    font_weight: int = 400
    font_size_token: str = ""
    line_height: float = 1.4
    effect_radius: float = 0.0
    effect_offset_y: float = 0.0
    grid_columns: int = 0


@dataclass(frozen=True, slots=True)
class ComponentSetSpec:
    """A component set before it is grounded."""

    key: str
    name: str
    variants: tuple[str, ...]
    boolean_props: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PageSectionSpec:
    """One section of a storefront page — the component instance to place."""

    section: str
    component_key: str
    variant: str


@dataclass(frozen=True, slots=True)
class StorefrontPageSpec:
    """One storefront page and its ordered sections."""

    name: str
    sections: tuple[PageSectionSpec, ...] = field(default_factory=tuple)


def _lit(key: str, vtype: VariableType, scopes, light: str, dark: str | None = None) -> VariableSpec:
    values = {"Light": ("lit", light), "Dark": ("lit", dark if dark is not None else light)}
    return VariableSpec(key=key, type=vtype, scopes=tuple(scopes), values=values)


def _alias(key: str, scopes, light_ref: str, dark_ref: str) -> VariableSpec:
    return VariableSpec(
        key=key, type=VariableType.COLOR, scopes=tuple(scopes),
        values={"Light": ("ref", light_ref), "Dark": ("ref", dark_ref)},
    )


def _val(key: str, vtype: VariableType, scopes, value: str) -> VariableSpec:
    return VariableSpec(key=key, type=vtype, scopes=tuple(scopes), values={"Value": ("lit", value)})


# --------------------------------------------------------------------------- #
# Collections                                                                  #
# --------------------------------------------------------------------------- #
_C = VariableScope

_PRIMITIVES = CollectionSpec(
    kind=CollectionKind.PRIMITIVE,
    name="Primitives",
    modes=("Value",),
    variables=(
        _val("gray.0", VariableType.COLOR, (_C.ALL,), "#FFFFFF"),
        _val("gray.50", VariableType.COLOR, (_C.ALL,), "#F7F7F8"),
        _val("gray.200", VariableType.COLOR, (_C.ALL,), "#D9D9DE"),
        _val("gray.600", VariableType.COLOR, (_C.ALL,), "#4D4D55"),
        _val("gray.900", VariableType.COLOR, (_C.ALL,), "#0A0A0C"),
        _val("brand.500", VariableType.COLOR, (_C.ALL,), "#2B59FF"),
        _val("brand.600", VariableType.COLOR, (_C.ALL,), "#1E42CC"),
        _val("space.1", VariableType.FLOAT, (_C.GAP,), "4"),
        _val("space.2", VariableType.FLOAT, (_C.GAP,), "8"),
        _val("space.4", VariableType.FLOAT, (_C.GAP,), "16"),
        _val("space.6", VariableType.FLOAT, (_C.GAP,), "24"),
        _val("space.8", VariableType.FLOAT, (_C.GAP,), "32"),
        _val("space.12", VariableType.FLOAT, (_C.GAP,), "48"),
        _val("space.16", VariableType.FLOAT, (_C.GAP,), "64"),
        _val("radius.sm", VariableType.FLOAT, (_C.CORNER_RADIUS,), "4"),
        _val("radius.md", VariableType.FLOAT, (_C.CORNER_RADIUS,), "8"),
        _val("radius.lg", VariableType.FLOAT, (_C.CORNER_RADIUS,), "16"),
        _val("type.size.100", VariableType.FLOAT, (_C.FONT_SIZE,), "12"),
        _val("type.size.300", VariableType.FLOAT, (_C.FONT_SIZE,), "16"),
        _val("type.size.600", VariableType.FLOAT, (_C.FONT_SIZE,), "32"),
        _val("type.size.700", VariableType.FLOAT, (_C.FONT_SIZE,), "40"),
    ),
)

_THEME = CollectionSpec(
    kind=CollectionKind.THEME,
    name="Theme",
    modes=("Light", "Dark"),
    variables=(
        _alias("color.text.default", (_C.FILL_COLOR,), "gray.900", "gray.50"),
        _alias("color.text.muted", (_C.FILL_COLOR,), "gray.600", "gray.200"),
        _alias("color.text.inverse", (_C.FILL_COLOR,), "gray.0", "gray.900"),
        _alias("color.bg.default", (_C.FILL_COLOR,), "gray.0", "gray.900"),
        _alias("color.bg.subtle", (_C.FILL_COLOR,), "gray.50", "gray.900"),
        _alias("color.bg.inverse", (_C.FILL_COLOR,), "gray.900", "gray.0"),
        _alias("color.action.primary", (_C.FILL_COLOR,), "brand.500", "brand.500"),
        _alias("color.action.primary.hover", (_C.FILL_COLOR,), "brand.600", "brand.600"),
        _alias("color.border.default", (_C.STROKE_COLOR,), "gray.200", "gray.600"),
    ),
)

_DEVICE = CollectionSpec(
    kind=CollectionKind.DEVICE,
    name="Device",
    modes=("Desktop", "Tablet", "Mobile"),
    variables=(
        VariableSpec(
            key="grid.columns", type=VariableType.FLOAT, scopes=(_C.WIDTH_HEIGHT,),
            values={"Desktop": ("lit", "12"), "Tablet": ("lit", "8"), "Mobile": ("lit", "4")},
        ),
        VariableSpec(
            key="container.width", type=VariableType.FLOAT, scopes=(_C.WIDTH_HEIGHT,),
            values={"Desktop": ("lit", "1200"), "Tablet": ("lit", "768"), "Mobile": ("lit", "375")},
        ),
    ),
)

COLLECTIONS: tuple[CollectionSpec, ...] = (_PRIMITIVES, _THEME, _DEVICE)

# --------------------------------------------------------------------------- #
# Styles                                                                        #
# --------------------------------------------------------------------------- #
STYLES: tuple[StyleSpec, ...] = (
    StyleSpec("Surface/Default", StyleType.FILL, color_token="color.bg.default"),
    StyleSpec("Surface/Subtle", StyleType.FILL, color_token="color.bg.subtle"),
    StyleSpec("Surface/Inverse", StyleType.FILL, color_token="color.bg.inverse"),
    StyleSpec("Action/Primary", StyleType.FILL, color_token="color.action.primary"),
    StyleSpec("Text/Default", StyleType.FILL, color_token="color.text.default"),
    StyleSpec("Heading/H1", StyleType.TEXT, font_weight=700, font_size_token="type.size.700",
              line_height=1.1),
    StyleSpec("Heading/H2", StyleType.TEXT, font_weight=700, font_size_token="type.size.600",
              line_height=1.2),
    StyleSpec("Body", StyleType.TEXT, font_weight=400, font_size_token="type.size.300",
              line_height=1.5),
    StyleSpec("Caption", StyleType.TEXT, font_weight=400, font_size_token="type.size.100",
              line_height=1.4),
    StyleSpec("Shadow/SM", StyleType.EFFECT, color_token="gray.900", effect_radius=2,
              effect_offset_y=1),
    StyleSpec("Shadow/MD", StyleType.EFFECT, color_token="gray.900", effect_radius=12,
              effect_offset_y=4),
    StyleSpec("Grid/12", StyleType.GRID, grid_columns=12),
)

# --------------------------------------------------------------------------- #
# Component sets                                                                #
# --------------------------------------------------------------------------- #
COMPONENT_SETS: tuple[ComponentSetSpec, ...] = (
    ComponentSetSpec("header", "Header", ("sticky", "static")),
    ComponentSetSpec("navigation", "Navigation", ("horizontal", "vertical")),
    ComponentSetSpec("breadcrumbs", "Breadcrumbs", ("full", "collapsed")),
    ComponentSetSpec("hero", "Hero", ("full-bleed", "split")),
    ComponentSetSpec("usp_grid", "USP Grid", ("three-up", "four-up")),
    ComponentSetSpec("category_grid", "Category Grid", ("two-up", "three-up")),
    ComponentSetSpec("product_grid", "Product Grid", ("dense", "comfortable")),
    ComponentSetSpec("product_card", "Product Card", ("regular", "compact"),
                     boolean_props=("show_quick_add",)),
    ComponentSetSpec("product_gallery", "Product Gallery", ("stacked", "carousel")),
    ComponentSetSpec("product_information", "Product Information", ("stacked", "columns")),
    ComponentSetSpec("variant_picker", "Variant Picker", ("swatch", "dropdown")),
    ComponentSetSpec("sticky_add_to_cart", "Sticky Add To Cart", ("scroll", "always")),
    ComponentSetSpec("trust_badges", "Trust Badges", ("row", "grid")),
    ComponentSetSpec("reviews", "Reviews", ("list", "grid")),
    ComponentSetSpec("related_products", "Related Products", ("carousel", "grid")),
    ComponentSetSpec("recommendations", "Recommendations", ("carousel", "grid")),
    ComponentSetSpec("cart_drawer", "Cart Drawer", ("right", "left")),
    ComponentSetSpec("checkout_blocks", "Checkout Blocks", ("single", "multi")),
    ComponentSetSpec("forms", "Forms", ("default", "error", "success")),
    ComponentSetSpec("search", "Search", ("inline", "overlay")),
    ComponentSetSpec("filters", "Filters", ("sidebar", "drawer")),
    ComponentSetSpec("pagination", "Pagination", ("numbered", "compact")),
    ComponentSetSpec("footer", "Footer", ("multi-column", "compact")),
    ComponentSetSpec("newsletter", "Newsletter", ("inline", "banner")),
    ComponentSetSpec("account", "Account", ("dashboard", "list")),
    ComponentSetSpec("order_timeline", "Order Timeline", ("vertical", "horizontal")),
    ComponentSetSpec("sorting", "Sorting", ("dropdown", "inline")),
    ComponentSetSpec("testimonials", "Testimonials", ("carousel", "grid")),
)

# --------------------------------------------------------------------------- #
# Storefront pages                                                             #
# --------------------------------------------------------------------------- #

def _s(section: str, component: str, variant: str) -> PageSectionSpec:
    return PageSectionSpec(section=section, component_key=component, variant=variant)


STOREFRONT_PAGES: tuple[StorefrontPageSpec, ...] = (
    StorefrontPageSpec("Homepage", (
        _s("Header", "header", "sticky"),
        _s("Hero", "hero", "full-bleed"),
        _s("USPs", "usp_grid", "three-up"),
        _s("Categories", "category_grid", "three-up"),
        _s("Featured Products", "product_grid", "dense"),
        _s("Testimonials", "testimonials", "carousel"),
        _s("Newsletter", "newsletter", "inline"),
        _s("Footer", "footer", "multi-column"),
    )),
    StorefrontPageSpec("Collection", (
        _s("Header", "header", "sticky"),
        _s("Breadcrumbs", "breadcrumbs", "collapsed"),
        _s("Filters", "filters", "sidebar"),
        _s("Sorting", "sorting", "dropdown"),
        _s("Product Grid", "product_grid", "dense"),
        _s("Pagination", "pagination", "numbered"),
        _s("Footer", "footer", "multi-column"),
    )),
    StorefrontPageSpec("Product", (
        _s("Header", "header", "sticky"),
        _s("Breadcrumbs", "breadcrumbs", "collapsed"),
        _s("Gallery", "product_gallery", "stacked"),
        _s("Information", "product_information", "columns"),
        _s("Variant Picker", "variant_picker", "swatch"),
        _s("Add To Cart", "sticky_add_to_cart", "scroll"),
        _s("Trust", "trust_badges", "row"),
        _s("Reviews", "reviews", "list"),
        _s("Related", "related_products", "carousel"),
        _s("Footer", "footer", "multi-column"),
    )),
    StorefrontPageSpec("Cart", (
        _s("Header", "header", "sticky"),
        _s("Cart", "forms", "default"),
        _s("Recommendations", "recommendations", "carousel"),
        _s("Trust", "trust_badges", "row"),
        _s("Footer", "footer", "multi-column"),
    )),
    StorefrontPageSpec("Checkout", (
        _s("Header", "header", "static"),
        _s("Checkout", "checkout_blocks", "single"),
        _s("Trust", "trust_badges", "row"),
        _s("Footer", "footer", "compact"),
    )),
    StorefrontPageSpec("Search", (
        _s("Header", "header", "sticky"),
        _s("Search", "search", "inline"),
        _s("Filters", "filters", "drawer"),
        _s("Results", "product_grid", "dense"),
        _s("Pagination", "pagination", "numbered"),
        _s("Footer", "footer", "multi-column"),
    )),
    StorefrontPageSpec("Account", (
        _s("Header", "header", "sticky"),
        _s("Account", "account", "dashboard"),
        _s("Orders", "order_timeline", "vertical"),
        _s("Footer", "footer", "multi-column"),
    )),
)
