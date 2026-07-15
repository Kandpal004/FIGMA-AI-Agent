"""The Variable Binding model — a node property bound to a variable.

A :class:`VariableBinding` records that a node property (a fill, a gap, a corner radius, a font
size, …) is driven by a variable rather than a literal. The scope of the target variable must
permit that property — you cannot bind a colour variable to a corner radius — and the binding
resolver checks each target against the declared collections. This is what makes a Figma file
variable-driven instead of hard-coded.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.shared.value_objects import VariableScope

__all__ = ["BindableProperty", "InvalidBindingError", "VariableBinding"]

_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidBindingError(DesignDirectorError):
    """Raised when a variable binding is constructed with invalid data."""

    code = "invalid_figma_design_binding"
    http_status = 422


class BindableProperty(str):
    """A node property name that a variable can bind to (e.g. 'fill', 'itemSpacing')."""


# The scope a given bindable property requires of its variable.
_PROPERTY_SCOPE: dict[str, VariableScope] = {
    "fill": VariableScope.FILL_COLOR,
    "stroke": VariableScope.STROKE_COLOR,
    "itemSpacing": VariableScope.GAP,
    "paddingTop": VariableScope.GAP,
    "paddingRight": VariableScope.GAP,
    "paddingBottom": VariableScope.GAP,
    "paddingLeft": VariableScope.GAP,
    "cornerRadius": VariableScope.CORNER_RADIUS,
    "width": VariableScope.WIDTH_HEIGHT,
    "height": VariableScope.WIDTH_HEIGHT,
    "fontSize": VariableScope.FONT_SIZE,
    "lineHeight": VariableScope.LINE_HEIGHT,
    "letterSpacing": VariableScope.LETTER_SPACING,
    "opacity": VariableScope.OPACITY,
    "characters": VariableScope.TEXT_CONTENT,
}


@dataclass(frozen=True, slots=True)
class VariableBinding:
    """A node property bound to a variable by key.

    Attributes:
        property: The node property name (e.g. ``"fill"``, ``"itemSpacing"``, ``"cornerRadius"``).
        variable_key: The key of the variable driving the property.
    """

    property: str
    variable_key: str

    def __post_init__(self) -> None:
        prop = self.property.strip()
        if prop not in _PROPERTY_SCOPE:
            raise InvalidBindingError(
                f"Unknown bindable property {self.property!r}.",
                details={"property": self.property, "known": sorted(_PROPERTY_SCOPE)},
            )
        key = self.variable_key.strip().lower()
        if not _KEY.match(key):
            raise InvalidBindingError(
                "VariableBinding.variable_key must be a dotted variable key.",
                details={"variable_key": self.variable_key},
            )
        object.__setattr__(self, "property", prop)
        object.__setattr__(self, "variable_key", key)

    @property
    def required_scope(self) -> VariableScope:
        """The scope the target variable must permit for this binding to be valid."""
        return _PROPERTY_SCOPE[self.property]
