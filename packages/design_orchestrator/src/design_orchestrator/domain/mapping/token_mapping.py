"""The token mapping — which Design-System tokens each section binds.

A :class:`TokenMapping` is the resolved, immutable binding from each section (by
:class:`SectionPlanId`) to the Design-System token keys it consumes. It is the frozen result of
the selection resolver having checked every binding against the live Design System, so a future
Figma phase can bind Figma Variables straight from it without re-resolving. Keyed by section, so
it joins cleanly onto the component tree and the section plans.

Pure domain: standard library, the shared-kernel error base, DO ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.ids import SectionPlanId

__all__ = ["InvalidTokenMappingError", "TokenMapping"]

_TOKEN_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidTokenMappingError(DesignDirectorError):
    """Raised when a token mapping is constructed with invalid data."""

    code = "invalid_design_orchestrator_token_mapping"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TokenMapping:
    """The resolved binding from each section to the token keys it consumes.

    Attributes:
        bindings: Section id -> the unique, ordered token keys it binds (each non-empty).
    """

    bindings: Mapping[SectionPlanId, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        resolved: dict[SectionPlanId, tuple[str, ...]] = {}
        for section_id, keys in self.bindings.items():
            cleaned = tuple(dict.fromkeys(k.strip().lower() for k in keys if k and k.strip()))
            if not cleaned:
                raise InvalidTokenMappingError(
                    "A token mapping entry must bind at least one token.",
                    details={"section": str(section_id)},
                )
            for key in cleaned:
                if not _TOKEN_KEY.match(key):
                    raise InvalidTokenMappingError(
                        f"Token binding {key!r} is not a valid dotted token key.",
                        details={"section": str(section_id)},
                    )
            resolved[section_id] = cleaned
        object.__setattr__(self, "bindings", MappingProxyType(resolved))

    def __len__(self) -> int:
        return len(self.bindings)

    def __iter__(self):
        return iter(self.bindings.items())

    def has(self, section_id: SectionPlanId) -> bool:
        return section_id in self.bindings

    def for_section(self, section_id: SectionPlanId) -> tuple[str, ...]:
        return self.bindings.get(section_id, ())

    @property
    def all_token_keys(self) -> frozenset[str]:
        return frozenset(k for keys in self.bindings.values() for k in keys)
