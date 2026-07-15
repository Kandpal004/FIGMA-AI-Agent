"""The Variant Mapping — which component set and variant each instance selects.

A :class:`VariantMapping` is the resolved, immutable projection from each INSTANCE node (by
:class:`FigmaNodeId`) to the component-set key and variant name it instantiates. It is the frozen
result of the binding resolver having confirmed each instance references a real component set and
a variant that set declares, so a downstream renderer can set Figma component properties straight
from it.

Pure domain: standard library, the shared-kernel error base, FD ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import FigmaNodeId

__all__ = ["InstanceSelection", "InvalidVariantMappingError", "VariantMapping"]

_NAME = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidVariantMappingError(DesignDirectorError):
    """Raised when a variant mapping is constructed with invalid data."""

    code = "invalid_figma_design_variant_mapping"
    http_status = 422


@dataclass(frozen=True, slots=True)
class InstanceSelection:
    """The component set and variant an instance selects.

    Attributes:
        component_set_key: The component-set key instantiated.
        variant_name: The variant selected (a lower-case identifier the set declares).
    """

    component_set_key: str
    variant_name: str

    def __post_init__(self) -> None:
        key = self.component_set_key.strip().lower()
        variant = self.variant_name.strip().lower()
        if not _NAME.match(key):
            raise InvalidVariantMappingError(
                "InstanceSelection.component_set_key must be a lower-case identifier.",
                details={"key": self.component_set_key},
            )
        if not _NAME.match(variant):
            raise InvalidVariantMappingError(
                "InstanceSelection.variant_name must be a lower-case identifier.",
                details={"variant_name": self.variant_name},
            )
        object.__setattr__(self, "component_set_key", key)
        object.__setattr__(self, "variant_name", variant)


@dataclass(frozen=True, slots=True)
class VariantMapping:
    """The resolved binding from each instance to its component set and variant.

    Attributes:
        selections: Node id -> the instance selection for that node.
    """

    selections: Mapping[FigmaNodeId, InstanceSelection] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.selections, MappingProxyType):
            object.__setattr__(self, "selections", MappingProxyType(dict(self.selections)))

    def __len__(self) -> int:
        return len(self.selections)

    def __iter__(self):
        return iter(self.selections.items())

    def has(self, node_id: FigmaNodeId) -> bool:
        return node_id in self.selections

    def for_node(self, node_id: FigmaNodeId) -> InstanceSelection | None:
        return self.selections.get(node_id)
