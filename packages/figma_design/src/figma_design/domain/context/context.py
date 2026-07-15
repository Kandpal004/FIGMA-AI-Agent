"""Figma Design inputs — the neutral context the engine models over.

These value objects capture the *given* context of a Figma-modelling engagement — the project,
the brief (the device classes to render, whether dark mode is required), and the
:class:`SourceRefs` (the exact upstream artifacts the model is built from) — in the engine's own
vocabulary, independent of any upstream engine's models. Infrastructure adapters translate the
Design Orchestrator, Design System, Component Intelligence, Design Language, and Creative Director
engines into evidence and neutral references; the domain never imports those engines — nor any
Figma SDK, MCP client, or HTTP library.

:class:`SourceRefs` is the reproducibility anchor: it records which execution plan, which design
system, and which composition the model was built from, so a model can be re-derived and its
provenance audited across re-runs.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.shared.value_objects import DeviceClass

__all__ = [
    "FigmaBrief",
    "FigmaBriefDefaults",
    "InvalidContextError",
    "ProjectContext",
    "SourceRefs",
]


class InvalidContextError(DesignDirectorError):
    """Raised when Figma-model context is constructed with invalid data."""

    code = "invalid_figma_design_context"
    http_status = 422


class FigmaBriefDefaults:
    """The default scope a storefront Figma model covers."""

    DEVICES: tuple[DeviceClass, ...] = (
        DeviceClass.DESKTOP,
        DeviceClass.TABLET,
        DeviceClass.MOBILE,
    )


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a Figma model serves.

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
    """The exact upstream artifacts a Figma model is built from.

    Every field is a neutral string reference (typically the ``str`` of an upstream typed id), so
    the domain records reproducibility anchors without importing any upstream engine. All are
    optional — the more that are present, the tighter the provenance audit.

    Attributes:
        execution_plan_id: The Design Orchestrator (P17) execution plan version.
        design_system_spec_id: The Design System (P16) spec version.
        component_spec_id: The Component Intelligence (P15) composition version.
        design_language_spec_id: The Design Language (P14) spec version.
        creative_director_review_id: The Creative Director (P13) review.
    """

    execution_plan_id: str | None = None
    design_system_spec_id: str | None = None
    component_spec_id: str | None = None
    design_language_spec_id: str | None = None
    creative_director_review_id: str | None = None


@dataclass(frozen=True, slots=True)
class FigmaBrief:
    """The storefront whose Figma model is being generated.

    Attributes:
        product_category: The product/offer category.
        devices: The device classes the model renders frames for.
        dark_mode: Whether a dark theme mode is required (mode parity is enforced when true).
    """

    product_category: str
    devices: tuple[DeviceClass, ...] = FigmaBriefDefaults.DEVICES
    dark_mode: bool = True

    def __post_init__(self) -> None:
        if not self.product_category or not self.product_category.strip():
            raise InvalidContextError("FigmaBrief.product_category must be non-empty.")
        devices = tuple(dict.fromkeys(self.devices)) or FigmaBriefDefaults.DEVICES
        if DeviceClass.DESKTOP not in devices:
            devices = (DeviceClass.DESKTOP, *devices)
        object.__setattr__(self, "devices", devices)

    @property
    def is_multi_device(self) -> bool:
        return len(self.devices) > 1
