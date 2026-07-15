"""Component Intelligence inputs — the neutral context the engine composes over.

These value objects capture the *given* context of a composition engagement — the project and
the brief (the pages in scope, typically inherited from the wireframe plan) — in the engine's
own vocabulary, independent of any upstream engine's models. Infrastructure adapters translate
the Phase-14 Design Language, Phase-13 Creative Director, Phase-12 Wireframe, and the strategy
engines into evidence; the domain never imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.value_objects import PageType

__all__ = ["CompositionBrief", "CompositionBriefDefaults", "InvalidContextError", "ProjectContext"]


class InvalidContextError(DesignDirectorError):
    """Raised when composition context is constructed with invalid data."""

    code = "invalid_component_intelligence_context"
    http_status = 422


class CompositionBriefDefaults:
    """The default set of page types a storefront composition covers."""

    PAGES: tuple[PageType, ...] = (
        PageType.HOMEPAGE,
        PageType.COLLECTION,
        PageType.PRODUCT,
        PageType.CART,
        PageType.CHECKOUT,
        PageType.SEARCH,
        PageType.ACCOUNT,
    )


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a composition serves.

    Attributes:
        project_id: The owning project (UUID string).
        platform: The commerce platform (e.g. "shopify_plus", "adobe_commerce").
        market: The market segment (e.g. "premium", "mass").
        country: The primary country/region.
        tenant_id: The viewer's tenant, for Knowledge scope resolution (UUID string).
    """

    project_id: str
    platform: str = ""
    market: str = ""
    country: str = ""
    tenant_id: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id or not self.project_id.strip():
            raise InvalidContextError("ProjectContext.project_id must be non-empty.")


@dataclass(frozen=True, slots=True)
class CompositionBrief:
    """The storefront whose component composition is being intelligently assembled.

    Attributes:
        product_category: The product/offer category.
        pages: The page types in scope (defaults to the storefront set).
        catalog_scale: A hint at catalog size ("small", "medium", "large").
        has_blog: Whether the storefront has a blog.
        has_wishlist: Whether the storefront has a wishlist.
    """

    product_category: str
    pages: tuple[PageType, ...] = CompositionBriefDefaults.PAGES
    catalog_scale: str = "medium"
    has_blog: bool = False
    has_wishlist: bool = False

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("CompositionBrief.product_category must be non-empty.")
        pages = tuple(dict.fromkeys(self.pages)) or CompositionBriefDefaults.PAGES
        object.__setattr__(self, "pages", pages)

    @property
    def is_large_catalog(self) -> bool:
        return self.catalog_scale.strip().lower() == "large"
