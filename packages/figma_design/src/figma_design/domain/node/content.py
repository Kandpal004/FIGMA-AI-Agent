"""Typed node content — the per-type payload a Figma node carries.

Different node types carry different content: a TEXT node carries :class:`TextContent`, an IMAGE
node carries an :class:`ImageRef`, and an INSTANCE node carries an :class:`InstanceRef` naming its
component set, the variant selected, and any component-property overrides. Modelling these as
distinct value objects keeps the node union type-safe and lets the tree aggregate check, per node
type, that the right content is present and well-formed.

Pure domain: standard library, the shared-kernel error base, FD ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import FigmaComponentSetId, StyleId

__all__ = ["ImageRef", "InstanceRef", "InvalidContentError", "TextContent"]

_VARIANT = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidContentError(DesignDirectorError):
    """Raised when node content is constructed with invalid data."""

    code = "invalid_figma_design_content"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TextContent:
    """The content of a TEXT node.

    Attributes:
        characters: The text content.
        text_style_ref: The published text style the node uses, if any.
    """

    characters: str
    text_style_ref: StyleId | None = None

    def __post_init__(self) -> None:
        if self.characters is None:
            raise InvalidContentError("TextContent.characters must not be None.")


@dataclass(frozen=True, slots=True)
class ImageRef:
    """The content of an IMAGE node.

    Attributes:
        image_ref: An opaque image reference (resolved to a real asset by a future renderer).
        alt: Alt text for accessibility.
    """

    image_ref: str
    alt: str = ""

    def __post_init__(self) -> None:
        if not self.image_ref or not self.image_ref.strip():
            raise InvalidContentError("ImageRef.image_ref must be non-empty.")
        object.__setattr__(self, "image_ref", self.image_ref.strip())


@dataclass(frozen=True, slots=True)
class InstanceRef:
    """The content of an INSTANCE node — which component set, variant, and overrides.

    Attributes:
        component_set_id: The component set this instance is an instance of.
        variant_name: The variant selected (a lower-case identifier the set declares).
        property_overrides: Component-property overrides (property name → value).
    """

    component_set_id: FigmaComponentSetId
    variant_name: str
    property_overrides: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        variant = self.variant_name.strip().lower()
        if not _VARIANT.match(variant):
            raise InvalidContentError(
                "InstanceRef.variant_name must be a lower-case identifier.",
                details={"variant_name": self.variant_name},
            )
        object.__setattr__(self, "variant_name", variant)
        overrides = {
            k.strip(): v.strip()
            for k, v in self.property_overrides.items()
            if k and k.strip()
        }
        object.__setattr__(self, "property_overrides", MappingProxyType(overrides))
