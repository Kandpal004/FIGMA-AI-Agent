"""Wireframe inputs — the neutral context the engine plans over.

These value objects capture the *given* context of a wireframe-planning engagement — the
storefront brief and the project — in the engine's own vocabulary, independent of any
upstream engine's models. Infrastructure adapters translate the Phase-11 Information
Architecture, Phase-10 UX, Phase-9 Psychology, Phase-8 Brand, and Phase-7 Business Strategy
outputs and user input into these; the domain never imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.value_objects import PageType

__all__ = ["InvalidContextError", "ProjectContext", "WireframeBrief", "WireframeBriefDefaults"]


class InvalidContextError(DesignDirectorError):
    """Raised when wireframe context is constructed with invalid data."""

    code = "invalid_wireframe_context"
    http_status = 422


class WireframeBriefDefaults:
    """The default set of page types a storefront wireframe plan covers."""

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
    """The project a wireframe plan serves.

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
class WireframeBrief:
    """The storefront whose wireframe execution plan is being produced.

    Attributes:
        product_category: The product/offer category.
        pages: The page types in scope (defaults to the storefront set).
        catalog_scale: A hint at catalog size ("small", "medium", "large").
        has_blog: Whether the storefront has a blog.
        has_landing: Whether the storefront has campaign landing pages.
    """

    product_category: str
    pages: tuple[PageType, ...] = WireframeBriefDefaults.PAGES
    catalog_scale: str = "medium"
    has_blog: bool = False
    has_landing: bool = False

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("WireframeBrief.product_category must be non-empty.")
        pages = tuple(dict.fromkeys(self.pages)) or WireframeBriefDefaults.PAGES
        object.__setattr__(self, "pages", pages)

    @property
    def is_large_catalog(self) -> bool:
        return self.catalog_scale.strip().lower() == "large"
