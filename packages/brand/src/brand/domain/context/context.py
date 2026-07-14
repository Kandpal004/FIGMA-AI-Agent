"""Brand inputs — the neutral context the engine reasons over.

These value objects capture the *given* context of a brand engagement — the brand brief
and the project — in the engine's own vocabulary, independent of any upstream engine's
models. Infrastructure adapters translate the Phase-7 Business Strategy directive and
user input into these; the domain never imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.value_objects import BrandCategory

__all__ = ["BrandBrief", "InvalidContextError", "ProjectContext"]


class InvalidContextError(DesignDirectorError):
    """Raised when brand context is constructed with invalid data."""

    code = "invalid_brand_context"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a brand strategy serves.

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
class BrandBrief:
    """The brand a strategy is built for.

    Attributes:
        name: The brand name.
        industry: The industry/vertical.
        maturity: Brand maturity (e.g. "startup", "growth", "established").
        category_hint: An optional stated primary brand category.
        descriptors: Free-form brand descriptors/adjectives the brand already uses.
        aspirations: What the brand wants to become / stand for.
    """

    name: str
    industry: str = ""
    maturity: str = ""
    category_hint: BrandCategory | None = None
    descriptors: tuple[str, ...] = ()
    aspirations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidContextError("BrandBrief.name must be non-empty.")
        object.__setattr__(self, "descriptors", tuple(self.descriptors))
        object.__setattr__(self, "aspirations", tuple(self.aspirations))
