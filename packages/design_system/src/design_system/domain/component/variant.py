"""Component variant machinery — properties, variants, states, and responsive behaviour.

For every component the design system defines *how it varies*: its :class:`ComponentProperty`
set (the variant/boolean/text/token/number knobs a consumer can set), its named
:class:`ComponentVariant` combinations, its per-state :class:`ComponentStateSpec` (which of the
ten states it supports and the tokens each activates), and its :class:`ResponsiveSpec` (how it
adapts across breakpoints). These are the platform-neutral behavioural contract every future UI
must honour; the platform mappings (:mod:`mapping`) translate them per platform.

Pure domain: standard library, the shared-kernel error base, token state, and shared value
objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.token.state import StateTokens
from design_system.domain.shared.value_objects import (
    Breakpoint,
    PropertyType,
    StateKind,
)

__all__ = [
    "ComponentProperty",
    "ComponentStateSpec",
    "ComponentVariant",
    "InvalidVariantError",
    "ResponsiveSpec",
]

_NAME = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidVariantError(DesignDirectorError):
    """Raised when component variant data is constructed with invalid data."""

    code = "invalid_design_system_variant"
    http_status = 422


def _name(value: str, what: str) -> str:
    normalized = value.strip().lower()
    if not _NAME.match(normalized):
        raise InvalidVariantError(
            f"{what} must be a lower-case identifier (got {value!r}).", details={"value": value}
        )
    return normalized


@dataclass(frozen=True, slots=True)
class ComponentProperty:
    """A single configurable knob on a component.

    Attributes:
        name: The property name (e.g. ``"variant"``, ``"size"``, ``"loading"``).
        type: The property type (variant / boolean / text / token / number).
        options: The allowed values for a ``VARIANT`` property (e.g. ``("primary", "secondary")``).
            Required and non-empty for ``VARIANT``; must be empty for all other types.
        default: The default value, if any (must be among ``options`` for a ``VARIANT``).
        required: Whether a consumer must supply this property.
    """

    name: str
    type: PropertyType
    options: tuple[str, ...] = ()
    default: str | None = None
    required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _name(self.name, "ComponentProperty.name"))
        options = tuple(dict.fromkeys(o.strip() for o in self.options if o and o.strip()))
        if self.type is PropertyType.VARIANT:
            if len(options) < 2:
                raise InvalidVariantError(
                    "A VARIANT property must offer at least two options.",
                    details={"name": self.name},
                )
        elif options:
            raise InvalidVariantError(
                "Only VARIANT properties may define options.", details={"name": self.name}
            )
        if self.default is not None and self.type is PropertyType.VARIANT:
            if self.default not in options:
                raise InvalidVariantError(
                    "ComponentProperty.default must be one of its options.",
                    details={"name": self.name, "default": self.default},
                )
        object.__setattr__(self, "options", options)


@dataclass(frozen=True, slots=True)
class ComponentVariant:
    """A named, meaningful combination of property values.

    Attributes:
        name: The variant name (e.g. ``"primary-large"``).
        property_values: The property→value assignments that define this variant.
        description: What this variant is for.
    """

    name: str
    property_values: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _name(self.name, "ComponentVariant.name"))
        values = {
            _name(k, "property"): v.strip()
            for k, v in self.property_values.items()
            if k and k.strip() and v and v.strip()
        }
        if not values:
            raise InvalidVariantError(
                "A ComponentVariant must assign at least one property value.",
                details={"name": self.name},
            )
        object.__setattr__(self, "property_values", MappingProxyType(values))


@dataclass(frozen=True, slots=True)
class ComponentStateSpec:
    """The states a component supports and the tokens each activates.

    Attributes:
        states: One :class:`StateTokens` per supported state. Must include ``DEFAULT`` and be
            unique by state.
    """

    states: tuple[StateTokens, ...]

    def __post_init__(self) -> None:
        states = tuple(self.states)
        kinds = [s.state for s in states]
        if StateKind.DEFAULT not in kinds:
            raise InvalidVariantError("A component must define the DEFAULT state.")
        if len(set(kinds)) != len(kinds):
            raise InvalidVariantError("Component states must be unique by kind.")
        object.__setattr__(self, "states", states)

    @property
    def kinds(self) -> tuple[StateKind, ...]:
        return tuple(s.state for s in self.states)

    def supports(self, state: StateKind) -> bool:
        return state in self.kinds


@dataclass(frozen=True, slots=True)
class ResponsiveSpec:
    """How a component adapts across the responsive breakpoints.

    Attributes:
        behavior: A mapping of breakpoint to a short behavioural note describing how the
            component adapts at that band (e.g. ``MOBILE`` → ``"stacked, full-width"``). Must
            include ``MOBILE`` (mobile-first) and cover each named band.
    """

    behavior: Mapping[Breakpoint, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        data = {
            bp: note.strip()
            for bp, note in self.behavior.items()
            if note and note.strip()
        }
        if Breakpoint.MOBILE not in data:
            raise InvalidVariantError(
                "ResponsiveSpec must be mobile-first (define MOBILE behaviour)."
            )
        object.__setattr__(self, "behavior", MappingProxyType(data))

    @property
    def bands(self) -> tuple[Breakpoint, ...]:
        return tuple(self.behavior.keys())
