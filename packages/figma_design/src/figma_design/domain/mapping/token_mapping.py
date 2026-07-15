"""The Token Mapping — which variables each node binds.

A :class:`TokenMapping` is the resolved, immutable projection from each node (by
:class:`FigmaNodeId`) to the variable keys its properties bind. It is the frozen result of the
binding resolver having checked every binding against the declared variable collections, so a
downstream renderer can bind Figma variables straight from it. Keyed by node, so it joins cleanly
onto the node tree.

Pure domain: standard library, the shared-kernel error base, FD ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import FigmaNodeId

__all__ = ["InvalidTokenMappingError", "TokenMapping"]

_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidTokenMappingError(DesignDirectorError):
    """Raised when a token mapping is constructed with invalid data."""

    code = "invalid_figma_design_token_mapping"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TokenMapping:
    """The resolved binding from each node to the variable keys it binds.

    Attributes:
        bindings: Node id -> the unique, ordered variable keys it binds.
    """

    bindings: Mapping[FigmaNodeId, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        resolved: dict[FigmaNodeId, tuple[str, ...]] = {}
        for node_id, keys in self.bindings.items():
            cleaned = tuple(dict.fromkeys(k.strip().lower() for k in keys if k and k.strip()))
            for key in cleaned:
                if not _KEY.match(key):
                    raise InvalidTokenMappingError(
                        f"Variable binding {key!r} is not a valid key.",
                        details={"node": str(node_id)},
                    )
            resolved[node_id] = cleaned
        object.__setattr__(self, "bindings", MappingProxyType(resolved))

    def __len__(self) -> int:
        return len(self.bindings)

    def __iter__(self):
        return iter(self.bindings.items())

    def has(self, node_id: FigmaNodeId) -> bool:
        return node_id in self.bindings

    def for_node(self, node_id: FigmaNodeId) -> tuple[str, ...]:
        return self.bindings.get(node_id, ())

    @property
    def all_variable_keys(self) -> frozenset[str]:
        return frozenset(k for keys in self.bindings.values() for k in keys)
