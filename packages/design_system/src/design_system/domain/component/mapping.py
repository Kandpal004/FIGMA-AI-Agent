"""Platform mappings — how a platform-neutral component realises on each target platform.

Every :class:`~design_system.domain.component.spec.ComponentSpec` must carry a developer mapping
(the framework-neutral implementation contract), a Shopify mapping, and a Magento (Adobe
Commerce) mapping. A :class:`PlatformMapping` records, per platform, the concrete artefact a
component becomes there — a Shopify section/block/snippet with its schema settings, a Magento
container/block/template with its layout handle — plus the theme/section constraints that apply.

The design system does not *generate* that platform code; it specifies the contract the future
UI/codegen phase must satisfy, so a component is never realised inconsistently across platforms.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from design_system.domain.shared.value_objects import Platform

__all__ = ["InvalidMappingError", "PlatformMapping"]


class InvalidMappingError(DesignDirectorError):
    """Raised when a platform mapping is constructed with invalid data."""

    code = "invalid_design_system_mapping"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PlatformMapping:
    """How a component realises on one target platform.

    Attributes:
        platform: The target platform (generic developer contract, Shopify, or Magento).
        primitive: The platform artefact kind the component becomes (e.g. ``"section"``,
            ``"block"``, ``"snippet"`` on Shopify; ``"container"``, ``"block"``, ``"template"``
            on Magento; ``"component"`` for the generic developer contract).
        identifier: The platform-specific handle/name (e.g. ``"sections/product-card.liquid"``,
            ``"Magento_Catalog::product/list.phtml"``, ``"ProductCard"``).
        settings: The configurable settings this artefact exposes (Shopify schema settings,
            Magento layout arguments, or developer props), by name.
        capabilities: Platform capabilities the component relies on (e.g. ``"app-blocks"``,
            ``"section-groups"``, ``"ui-component"``).
        notes: Any platform-specific implementation guidance.
    """

    platform: Platform
    primitive: str
    identifier: str
    settings: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.primitive or not self.primitive.strip():
            raise InvalidMappingError(
                "PlatformMapping.primitive must be non-empty.",
                details={"platform": self.platform.value},
            )
        if not self.identifier or not self.identifier.strip():
            raise InvalidMappingError(
                "PlatformMapping.identifier must be non-empty.",
                details={"platform": self.platform.value},
            )
        object.__setattr__(self, "primitive", self.primitive.strip())
        object.__setattr__(self, "identifier", self.identifier.strip())
        object.__setattr__(
            self,
            "settings",
            tuple(dict.fromkeys(s.strip() for s in self.settings if s and s.strip())),
        )
        object.__setattr__(
            self,
            "capabilities",
            tuple(dict.fromkeys(c.strip() for c in self.capabilities if c and c.strip())),
        )
