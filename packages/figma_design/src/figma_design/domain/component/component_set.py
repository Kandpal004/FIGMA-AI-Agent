"""The Component Set model — a variant matrix a designer publishes to the library.

A :class:`FigmaComponentSet` is the Figma expression of a Design-System component spec: a named
set of :class:`ComponentProperty` axes and the :class:`FigmaComponent` variants across them. It is
what an INSTANCE node references (by set + variant name), so it is the anchor of the file's
component library.

It enforces variant integrity at construction: at least one VARIANT property, unique variant
names, and every variant assigning only declared properties with allowed values — a variant that
sets a property the set never declared, or a value outside its options, is rejected. A
:class:`ComponentSetCatalog` is the immutable, unique-by-key registry.

Pure domain: standard library, the shared-kernel error base, FD ids, the property/component value
objects, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.component.component import FigmaComponent
from figma_design.domain.component.property import ComponentProperty
from figma_design.domain.shared.ids import FigmaComponentSetId

__all__ = ["ComponentSetCatalog", "FigmaComponentSet", "InvalidComponentSetError"]

_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidComponentSetError(DesignDirectorError):
    """Raised when a component set or catalog violates a structural invariant."""

    code = "invalid_figma_design_component_set"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FigmaComponentSet:
    """A named variant matrix.

    Attributes:
        id: Component-set identity.
        key: The component key (e.g. "product_card"); unique within the catalog.
        name: A human-readable name.
        properties: The property axes (must include at least one VARIANT property).
        components: The variants across those axes (unique by name; each well-formed).
        citations: The evidence supporting this set (must resolve in the evidence graph).
    """

    id: FigmaComponentSetId
    key: str
    name: str
    properties: tuple[ComponentProperty, ...]
    components: tuple[FigmaComponent, ...]
    citations: tuple = ()

    def __post_init__(self) -> None:
        key = self.key.strip().lower()
        if not _KEY.match(key):
            raise InvalidComponentSetError(
                "FigmaComponentSet.key must be a lower-case identifier.",
                details={"key": self.key},
            )
        object.__setattr__(self, "key", key)
        if not self.name or not self.name.strip():
            raise InvalidComponentSetError("FigmaComponentSet.name must be non-empty.")
        object.__setattr__(self, "name", self.name.strip())

        props = {p.name: p for p in self.properties}
        if len(props) != len(self.properties):
            raise InvalidComponentSetError(
                "Component properties must be unique by name.", details={"key": self.key}
            )
        if not any(p.is_variant for p in self.properties):
            raise InvalidComponentSetError(
                "A component set must declare at least one VARIANT property.",
                details={"key": self.key},
            )
        components = tuple(self.components)
        if not components:
            raise InvalidComponentSetError(
                "A component set must have at least one variant.", details={"key": self.key}
            )
        names = [c.name for c in components]
        if len(set(names)) != len(names):
            raise InvalidComponentSetError(
                "Variant names must be unique.", details={"key": self.key}
            )
        self._validate_variants(props, components)
        object.__setattr__(self, "properties", tuple(self.properties))
        object.__setattr__(self, "components", components)
        object.__setattr__(self, "citations", tuple(self.citations))

    def _validate_variants(
        self, props: dict[str, ComponentProperty], components: tuple[FigmaComponent, ...]
    ) -> None:
        for component in components:
            for name, value in component.variant.property_values.items():
                prop = props.get(name)
                if prop is None:
                    raise InvalidComponentSetError(
                        f"Variant {component.name!r} assigns unknown property {name!r}.",
                        details={"key": self.key},
                    )
                if prop.is_variant and value not in prop.options:
                    raise InvalidComponentSetError(
                        f"Variant {component.name!r} assigns {name}={value!r}, "
                        "not among the property's options.",
                        details={"key": self.key, "options": list(prop.options)},
                    )

    @property
    def variant_names(self) -> frozenset[str]:
        return frozenset(c.name for c in self.components)

    @property
    def property_names(self) -> frozenset[str]:
        return frozenset(p.name for p in self.properties)

    @property
    def evidence_ids(self) -> tuple:
        return tuple(c.evidence_id for c in self.citations)

    def declares_variant(self, variant_name: str) -> bool:
        return variant_name in self.variant_names


@dataclass(frozen=True, slots=True)
class ComponentSetCatalog:
    """The immutable, unique-by-key registry of component sets."""

    items: Mapping[str, FigmaComponentSet] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def of(cls, sets: Iterable[FigmaComponentSet]) -> ComponentSetCatalog:
        mapping: dict[str, FigmaComponentSet] = {}
        for component_set in sets:
            if component_set.key in mapping:
                raise InvalidComponentSetError(
                    "Duplicate component-set key.", details={"key": component_set.key}
                )
            mapping[component_set.key] = component_set
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def has(self, key: str) -> bool:
        return key in self.items

    def get(self, key: str) -> FigmaComponentSet:
        component_set = self.items.get(key)
        if component_set is None:
            raise InvalidComponentSetError(
                f"No component set {key!r}.", details={"key": key}
            )
        return component_set

    def by_id(self, set_id: FigmaComponentSetId) -> FigmaComponentSet | None:
        for component_set in self.items.values():
            if component_set.id == set_id:
                return component_set
        return None

    def keys(self) -> tuple[str, ...]:
        return tuple(self.items.keys())
