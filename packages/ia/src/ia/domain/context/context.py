"""IA inputs — the neutral context the engine reasons over.

These value objects capture the *given* context of an IA engagement — the storefront brief
and the project — in the engine's own vocabulary, independent of any upstream engine's
models. Infrastructure adapters translate the Phase-10 UX, Phase-9 Psychology, Phase-8
Brand, and Phase-7 Business Strategy directives and user input into these; the domain never
imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.value_objects import PageType

__all__ = ["IABrief", "InvalidContextError", "ProjectContext"]


class InvalidContextError(DesignDirectorError):
    """Raised when IA context is constructed with invalid data."""

    code = "invalid_ia_context"
    http_status = 422


class IABriefDefaults:
    """The default set of page types a storefront IA covers."""

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
    """The project an IA serves.

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
class IABrief:
    """The storefront whose information architecture is being defined.

    Attributes:
        product_category: The product/offer category.
        pages: The page types in scope (defaults to the storefront set).
        catalog_scale: A hint at catalog size ("small", "medium", "large").
        has_blog: Whether the storefront has a blog.
        has_wishlist: Whether the storefront has a wishlist.
    """

    product_category: str
    pages: tuple[PageType, ...] = IABriefDefaults.PAGES
    catalog_scale: str = "medium"
    has_blog: bool = False
    has_wishlist: bool = False

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("IABrief.product_category must be non-empty.")
        pages = tuple(dict.fromkeys(self.pages)) or IABriefDefaults.PAGES
        object.__setattr__(self, "pages", pages)

    @property
    def is_large_catalog(self) -> bool:
        return self.catalog_scale.strip().lower() == "large"
