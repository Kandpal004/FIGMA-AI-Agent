"""Psychology inputs — the neutral context the engine reasons over.

These value objects capture the *given* context of a psychology engagement — the
product/offer brief and the project — in the engine's own vocabulary, independent of any
upstream engine's models. Infrastructure adapters translate the Phase-8 Brand and
Phase-7 Business Strategy directives and user input into these; the domain never imports
those engines.

Pure domain: standard library and the shared-kernel error base.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

__all__ = ["InvalidContextError", "ProjectContext", "PsychologyBrief"]


class InvalidContextError(DesignDirectorError):
    """Raised when psychology context is constructed with invalid data."""

    code = "invalid_psychology_context"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a psychology model serves.

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
class PsychologyBrief:
    """The offer whose buying psychology is being modelled.

    Attributes:
        product_category: The product/offer category.
        price_band: The price band (e.g. "premium", "value", "luxury").
        purchase_type: "considered" or "impulse" — the decision mode.
        purchase_risk: The customer's perceived risk register ("low"/"medium"/"high").
        descriptors: Free-form descriptors of the offer or customer.
    """

    product_category: str
    price_band: str = ""
    purchase_type: str = "considered"
    purchase_risk: str = "medium"
    descriptors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("PsychologyBrief.product_category must be non-empty.")
        object.__setattr__(self, "descriptors", tuple(self.descriptors))

    @property
    def is_high_risk(self) -> bool:
        return self.purchase_risk.strip().lower() == "high"
