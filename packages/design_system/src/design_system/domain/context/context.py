"""Design System inputs — the neutral context the engine specifies over.

These value objects capture the *given* context of a design-system engagement — the project and
the brief (the platforms in scope, the pages the system must cover, whether dark mode and RTL
are required) — in the engine's own vocabulary, independent of any upstream engine's models.
Infrastructure adapters translate the Phase-14 Design Language, Phase-15 Component Intelligence,
Phase-13 Creative Director, and the strategy/psychology/UX/IA/Wireframe engines into evidence;
the domain never imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_system.domain.shared.value_objects import Direction, PageType, Platform

__all__ = [
    "DesignSystemBrief",
    "DesignSystemBriefDefaults",
    "InvalidContextError",
    "ProjectContext",
]


class InvalidContextError(DesignDirectorError):
    """Raised when design-system context is constructed with invalid data."""

    code = "invalid_design_system_context"
    http_status = 422


class DesignSystemBriefDefaults:
    """The default scope a storefront design system covers."""

    PAGES: tuple[PageType, ...] = (
        PageType.HOMEPAGE,
        PageType.COLLECTION,
        PageType.PRODUCT,
        PageType.CART,
        PageType.CHECKOUT,
        PageType.SEARCH,
        PageType.ACCOUNT,
    )
    PLATFORMS: tuple[Platform, ...] = (Platform.SHOPIFY, Platform.MAGENTO)


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a design system serves.

    Attributes:
        project_id: The owning project (UUID string).
        platform: The primary commerce platform (e.g. "shopify_plus", "adobe_commerce").
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
class DesignSystemBrief:
    """The storefront whose design system is being specified.

    Attributes:
        product_category: The product/offer category.
        platforms: The target platforms every component must map to.
        pages: The page types the system must cover.
        directions: The text directions the system must support (LTR always; RTL when localized).
        dark_mode: Whether a dark theme is required (parity is always enforced when true).
        locales: The locales the system must support (BCP-47-ish tags), primary first.
    """

    product_category: str
    platforms: tuple[Platform, ...] = DesignSystemBriefDefaults.PLATFORMS
    pages: tuple[PageType, ...] = DesignSystemBriefDefaults.PAGES
    directions: tuple[Direction, ...] = (Direction.LTR,)
    dark_mode: bool = True
    locales: tuple[str, ...] = ("en",)

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("DesignSystemBrief.product_category must be non-empty.")
        platforms = tuple(dict.fromkeys(self.platforms)) or DesignSystemBriefDefaults.PLATFORMS
        pages = tuple(dict.fromkeys(self.pages)) or DesignSystemBriefDefaults.PAGES
        directions = tuple(dict.fromkeys(self.directions)) or (Direction.LTR,)
        if Direction.LTR not in directions:
            directions = (Direction.LTR, *directions)
        locales = tuple(dict.fromkeys(loc.strip().lower() for loc in self.locales if loc.strip()))
        if not locales:
            locales = ("en",)
        object.__setattr__(self, "platforms", platforms)
        object.__setattr__(self, "pages", pages)
        object.__setattr__(self, "directions", directions)
        object.__setattr__(self, "locales", locales)

    @property
    def requires_rtl(self) -> bool:
        return Direction.RTL in self.directions

    @property
    def is_multi_platform(self) -> bool:
        return len(self.platforms) > 1
