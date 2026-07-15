"""The Component Property model — the configurable knobs on a component set.

A :class:`ComponentProperty` is one property axis of a component set: a VARIANT (named options —
the variant matrix), a BOOLEAN (show/hide), a TEXT (overridable copy), or an INSTANCE_SWAP
(swappable nested instance). These are the Figma component properties a senior designer exposes so
a single component covers many states without duplicated layers.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.shared.value_objects import ComponentPropertyType

__all__ = ["ComponentProperty", "InvalidComponentPropertyError"]

_NAME = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidComponentPropertyError(DesignDirectorError):
    """Raised when a component property is constructed with invalid data."""

    code = "invalid_figma_design_component_property"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentProperty:
    """One configurable property of a component set.

    Attributes:
        name: The property name (e.g. ``"variant"``, ``"size"``, ``"loading"``).
        type: The property type (variant / boolean / text / instance_swap).
        options: The allowed values for a VARIANT property (>= 2); empty for other types.
        default: The default value, if any (must be among ``options`` for a VARIANT).
    """

    name: str
    type: ComponentPropertyType
    options: tuple[str, ...] = ()
    default: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip().lower()
        if not _NAME.match(name):
            raise InvalidComponentPropertyError(
                "ComponentProperty.name must be a lower-case identifier.",
                details={"name": self.name},
            )
        object.__setattr__(self, "name", name)
        options = tuple(dict.fromkeys(o.strip() for o in self.options if o and o.strip()))
        if self.type is ComponentPropertyType.VARIANT:
            if len(options) < 2:
                raise InvalidComponentPropertyError(
                    "A VARIANT property must offer at least two options.",
                    details={"name": self.name},
                )
        elif options:
            raise InvalidComponentPropertyError(
                "Only VARIANT properties may define options.", details={"name": self.name}
            )
        if (
            self.default is not None
            and self.type is ComponentPropertyType.VARIANT
            and self.default not in options
        ):
            raise InvalidComponentPropertyError(
                "ComponentProperty.default must be one of its options.",
                details={"name": self.name, "default": self.default},
            )
        object.__setattr__(self, "options", options)

    @property
    def is_variant(self) -> bool:
        return self.type is ComponentPropertyType.VARIANT
