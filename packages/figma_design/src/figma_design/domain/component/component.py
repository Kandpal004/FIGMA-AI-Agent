"""The Component model — one variant of a component set.

A :class:`VariantDefinition` names a variant and the property values that define it (e.g.
``"primary-large" → {variant: primary, size: large}``). A :class:`FigmaComponent` is one realised
variant: its definition plus an optional reference to the root node of its layer subtree on the
Components page. Component sets hold these; instances reference them by variant name.

Pure domain: standard library, the shared-kernel error base, FD ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import FigmaComponentId, FigmaNodeId

__all__ = ["FigmaComponent", "InvalidComponentError", "VariantDefinition"]

_NAME = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidComponentError(DesignDirectorError):
    """Raised when a component or variant definition is constructed with invalid data."""

    code = "invalid_figma_design_component"
    http_status = 422


@dataclass(frozen=True, slots=True)
class VariantDefinition:
    """A named variant and the property values that define it.

    Attributes:
        name: The variant name (a lower-case identifier).
        property_values: The property→value assignments that define this variant.
    """

    name: str
    property_values: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        name = self.name.strip().lower()
        if not _NAME.match(name):
            raise InvalidComponentError(
                "VariantDefinition.name must be a lower-case identifier.",
                details={"name": self.name},
            )
        object.__setattr__(self, "name", name)
        values = {
            k.strip().lower(): v.strip()
            for k, v in self.property_values.items()
            if k and k.strip() and v and v.strip()
        }
        if not values:
            raise InvalidComponentError(
                "A VariantDefinition must assign at least one property value.",
                details={"name": self.name},
            )
        object.__setattr__(self, "property_values", MappingProxyType(values))


@dataclass(frozen=True, slots=True)
class FigmaComponent:
    """One realised variant of a component set.

    Attributes:
        id: Component identity.
        variant: The variant this component realises.
        root_node_id: The root node of this variant's layer subtree, if built.
    """

    id: FigmaComponentId
    variant: VariantDefinition
    root_node_id: FigmaNodeId | None = None

    @property
    def name(self) -> str:
        return self.variant.name
