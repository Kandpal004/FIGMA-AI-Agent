"""Design Language inputs — the neutral context the engine designs over.

These value objects capture the *given* context of a design-language engagement — the project
and the brief — in the engine's own vocabulary, independent of any upstream engine's models.
Infrastructure adapters translate the Phase-13 Creative Director, Phase-9 Psychology, Phase-8
Brand, and Phase-7 Business Strategy outputs into evidence; the domain never imports those
engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.value_objects import IndustryPreset, LanguageArchetype

__all__ = ["DesignBrief", "InvalidContextError", "ProjectContext"]


class InvalidContextError(DesignDirectorError):
    """Raised when design-language context is constructed with invalid data."""

    code = "invalid_design_language_context"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a design language serves.

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
class DesignBrief:
    """The storefront whose visual language is being defined.

    Attributes:
        industry: The industry preset that seeds the language.
        product_category: The product/offer category.
        tier: The market tier ("mass", "premium", "luxury").
        preferred_archetype: A language archetype the caller hints at, if any — the engine
            still justifies or overrides it.
    """

    industry: IndustryPreset
    product_category: str = ""
    tier: str = "premium"
    preferred_archetype: LanguageArchetype | None = None

    @property
    def is_luxury(self) -> bool:
        return self.tier.strip().lower() == "luxury"
