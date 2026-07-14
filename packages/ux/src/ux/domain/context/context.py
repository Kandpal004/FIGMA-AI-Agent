"""UX inputs — the neutral context the engine reasons over.

These value objects capture the *given* context of a UX engagement — the offer/experience
brief and the project — in the engine's own vocabulary, independent of any upstream
engine's models. Infrastructure adapters translate the Phase-9 Psychology, Phase-8 Brand,
and Phase-7 Business Strategy directives and user input into these; the domain never
imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.value_objects import DeviceContext, PageKind

__all__ = ["InvalidContextError", "ProjectContext", "UXBrief"]


class InvalidContextError(DesignDirectorError):
    """Raised when UX context is constructed with invalid data."""

    code = "invalid_ux_context"
    http_status = 422


class UXBriefDefaults:
    """The default set of key pages a storefront UX strategy covers."""

    PAGES: tuple[PageKind, ...] = (
        PageKind.HOME,
        PageKind.CATEGORY,
        PageKind.PRODUCT,
        PageKind.CART,
        PageKind.CHECKOUT,
    )


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a UX strategy serves.

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
class UXBrief:
    """The experience whose UX strategy is being defined.

    Attributes:
        product_category: The product/offer category.
        pages: The key pages/surfaces in scope (defaults to the storefront set).
        device_priority: The primary device context to optimise for.
        platform_constraints: Free-form platform constraints the strategy must honour.
    """

    product_category: str
    pages: tuple[PageKind, ...] = UXBriefDefaults.PAGES
    device_priority: DeviceContext = DeviceContext.RESPONSIVE
    platform_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("UXBrief.product_category must be non-empty.")
        pages = tuple(dict.fromkeys(self.pages)) or UXBriefDefaults.PAGES
        object.__setattr__(self, "pages", pages)
        object.__setattr__(self, "platform_constraints", tuple(self.platform_constraints))

    @property
    def is_mobile_first(self) -> bool:
        return self.device_priority is DeviceContext.MOBILE
