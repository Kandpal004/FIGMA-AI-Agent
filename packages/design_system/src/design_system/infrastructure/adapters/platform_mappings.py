"""Platform-mapping factory — how each component realises on each target platform.

Given a component type, this factory produces the three mandatory :class:`PlatformMapping` s (the
generic developer contract, Shopify, and Magento/Adobe Commerce). The mappings are codified from
how each platform actually models storefront UI: Shopify sections/blocks/snippets with schema
settings and app-block/section-group capabilities; Magento containers/blocks/templates with
layout handles and UI-component capabilities. Components without a bespoke entry fall back to a
sensible default so every component is always fully mapped.

This is specification, not code generation — it records the contract a future UI/codegen phase
must satisfy, so a component is never realised inconsistently across platforms.

Pure infrastructure data + the domain mapping/value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_system.domain.component.mapping import PlatformMapping
from design_system.domain.shared.value_objects import ComponentType, Platform

__all__ = ["PlatformMappingFactory"]


@dataclass(frozen=True, slots=True)
class _Entry:
    """The per-platform artefact facts for one component."""

    shopify_primitive: str
    shopify_handle: str
    shopify_settings: tuple[str, ...]
    shopify_caps: tuple[str, ...]
    magento_primitive: str
    magento_handle: str
    magento_settings: tuple[str, ...]
    magento_caps: tuple[str, ...]


def _slug(component: ComponentType) -> str:
    return component.value.replace("_", "-")


def _pascal(component: ComponentType) -> str:
    return "".join(part.capitalize() for part in component.value.split("_"))


# Bespoke platform facts for the components that differ from the default shape.
_ENTRIES: dict[ComponentType, _Entry] = {
    ComponentType.HEADER: _Entry(
        "section-group", "sections/header-group.json", ("menu", "sticky", "logo"),
        ("section-groups", "app-blocks"),
        "block", "Magento_Theme::html/header.phtml", ("show_minicart", "logo_width"),
        ("layout-xml", "ui-component"),
    ),
    ComponentType.PRODUCT_INFORMATION: _Entry(
        "section", "sections/main-product.liquid",
        ("show_gallery", "enable_sticky_atc", "variant_style"), ("app-blocks",),
        "container", "catalog_product_view.xml:product.info.main",
        ("show_sku", "gallery_layout"), ("layout-xml", "ui-component"),
    ),
    ComponentType.PRODUCT_GRID: _Entry(
        "section", "sections/main-collection-product-grid.liquid",
        ("products_per_page", "columns_desktop", "enable_filtering"), ("app-blocks",),
        "block", "catalog_category_view.xml:category.products.list",
        ("column_count", "toolbar"), ("layout-xml",),
    ),
    ComponentType.CART_DRAWER: _Entry(
        "snippet", "snippets/cart-drawer.liquid", ("enable_upsell", "auto_open"),
        ("app-blocks",),
        "block", "Magento_Checkout::minicart.phtml", ("max_items_display",),
        ("ui-component", "knockout"),
    ),
    ComponentType.FOOTER: _Entry(
        "section-group", "sections/footer-group.json", ("newsletter", "payment_icons"),
        ("section-groups",),
        "block", "Magento_Theme::html/footer.phtml", ("show_newsletter",),
        ("layout-xml",),
    ),
}


class PlatformMappingFactory:
    """Builds the three required platform mappings for any component."""

    def build(self, component: ComponentType) -> dict[Platform, PlatformMapping]:
        entry = _ENTRIES.get(component)
        slug = _slug(component)
        pascal = _pascal(component)
        generic = PlatformMapping(
            platform=Platform.GENERIC,
            primitive="component",
            identifier=pascal,
            settings=("className", "children"),
            capabilities=("framework-agnostic",),
            notes="Token-driven, framework-neutral component contract.",
        )
        if entry is None:
            shopify = PlatformMapping(
                platform=Platform.SHOPIFY,
                primitive="section",
                identifier=f"sections/{slug}.liquid",
                settings=("padding_top", "padding_bottom", "color_scheme"),
                capabilities=("app-blocks",),
                notes="Themeable section with schema settings; values bound to tokens.",
            )
            magento = PlatformMapping(
                platform=Platform.MAGENTO,
                primitive="block",
                identifier=f"Magento_Theme::html/{slug}.phtml",
                settings=("css_class",),
                capabilities=("layout-xml",),
                notes="Layout-XML block; styling bound to token CSS variables.",
            )
        else:
            shopify = PlatformMapping(
                platform=Platform.SHOPIFY,
                primitive=entry.shopify_primitive,
                identifier=entry.shopify_handle,
                settings=entry.shopify_settings,
                capabilities=entry.shopify_caps,
                notes="Values bound to design tokens via CSS custom properties.",
            )
            magento = PlatformMapping(
                platform=Platform.MAGENTO,
                primitive=entry.magento_primitive,
                identifier=entry.magento_handle,
                settings=entry.magento_settings,
                capabilities=entry.magento_caps,
                notes="Styling bound to token CSS variables; behaviour via UI components.",
            )
        return {
            Platform.GENERIC: generic,
            Platform.SHOPIFY: shopify,
            Platform.MAGENTO: magento,
        }
