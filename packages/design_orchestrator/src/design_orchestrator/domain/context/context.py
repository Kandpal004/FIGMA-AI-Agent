"""Design Orchestrator inputs — the neutral context the engine plans over.

These value objects capture the *given* context of an orchestration engagement — the project,
the brief (the pages and platforms in scope), and the :class:`SourceRefs` (the exact upstream
artifacts the plan is built from) — in the engine's own vocabulary, independent of any upstream
engine's models. Infrastructure adapters translate the Design System, Component Intelligence,
Wireframe, Creative Director, and strategy engines into evidence and neutral references; the
domain never imports those engines.

:class:`SourceRefs` is the reproducibility anchor: it records which Design System spec version,
which Component Intelligence composition, which Wireframe plan, and which review the plan was
orchestrated from, so a plan can be re-derived and its provenance audited across re-runs.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.value_objects import PageType, Platform

__all__ = [
    "InvalidContextError",
    "OrchestrationBrief",
    "OrchestrationBriefDefaults",
    "ProjectContext",
    "SourceRefs",
]


class InvalidContextError(DesignDirectorError):
    """Raised when orchestration context is constructed with invalid data."""

    code = "invalid_design_orchestrator_context"
    http_status = 422


class OrchestrationBriefDefaults:
    """The default scope a storefront orchestration covers."""

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
    """The project an execution plan serves.

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
class SourceRefs:
    """The exact upstream artifacts an execution plan is orchestrated from.

    Every field is a neutral string reference (typically the ``str`` of an upstream typed id),
    so the domain records reproducibility anchors without importing any upstream engine. All are
    optional — a plan can be produced from whatever upstream context is available — but the more
    that are present, the tighter the provenance audit.

    Attributes:
        design_system_spec_id: The Design System (P16) spec version.
        component_spec_id: The Component Intelligence (P15) composition version.
        design_language_spec_id: The Design Language (P14) spec version.
        creative_director_review_id: The Creative Director (P13) review.
        wireframe_plan_id: The Wireframe (P12) plan.
        ia_report_id: The Information Architecture (P11) report.
    """

    design_system_spec_id: str | None = None
    component_spec_id: str | None = None
    design_language_spec_id: str | None = None
    creative_director_review_id: str | None = None
    wireframe_plan_id: str | None = None
    ia_report_id: str | None = None


@dataclass(frozen=True, slots=True)
class OrchestrationBrief:
    """The storefront whose design execution is being planned.

    Attributes:
        product_category: The product/offer category.
        platforms: The target platforms the plan is realised on.
        pages: The page types in scope (defaults to the storefront set).
    """

    product_category: str
    platforms: tuple[Platform, ...] = OrchestrationBriefDefaults.PLATFORMS
    pages: tuple[PageType, ...] = OrchestrationBriefDefaults.PAGES

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("OrchestrationBrief.product_category must be non-empty.")
        platforms = tuple(dict.fromkeys(self.platforms)) or OrchestrationBriefDefaults.PLATFORMS
        pages = tuple(dict.fromkeys(self.pages)) or OrchestrationBriefDefaults.PAGES
        object.__setattr__(self, "platforms", platforms)
        object.__setattr__(self, "pages", pages)

    @property
    def is_multi_platform(self) -> bool:
        return len(self.platforms) > 1
