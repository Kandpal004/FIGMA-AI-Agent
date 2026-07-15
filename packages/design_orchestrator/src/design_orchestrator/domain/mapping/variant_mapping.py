"""The variant mapping — which component variant each section instantiates.

A :class:`VariantMapping` is the resolved, immutable binding from each section (by
:class:`SectionPlanId`) to the ``(component, variant_name)`` pair the orchestrator chose. It is
the frozen result of the selection resolver having confirmed each variant is one the Design
System component spec declares, so a future Figma phase can set Component Properties straight
from it. Keyed by section, so it joins cleanly onto the component tree and the section plans.

Pure domain: standard library, the shared-kernel error base, DO ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.ids import SectionPlanId
from design_orchestrator.domain.shared.value_objects import ComponentType

__all__ = ["InvalidVariantMappingError", "VariantChoice", "VariantMapping"]

_VARIANT = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidVariantMappingError(DesignDirectorError):
    """Raised when a variant mapping is constructed with invalid data."""

    code = "invalid_design_orchestrator_variant_mapping"
    http_status = 422


@dataclass(frozen=True, slots=True)
class VariantChoice:
    """The component and variant chosen for a section.

    Attributes:
        component: The component instantiated.
        variant_name: The variant chosen (a lower-case identifier the component declares).
    """

    component: ComponentType
    variant_name: str

    def __post_init__(self) -> None:
        variant = self.variant_name.strip().lower()
        if not _VARIANT.match(variant):
            raise InvalidVariantMappingError(
                "VariantChoice.variant_name must be a lower-case identifier.",
                details={"variant_name": self.variant_name},
            )
        object.__setattr__(self, "variant_name", variant)


@dataclass(frozen=True, slots=True)
class VariantMapping:
    """The resolved binding from each section to its component and variant.

    Attributes:
        choices: Section id -> the variant choice for that section.
    """

    choices: Mapping[SectionPlanId, VariantChoice] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.choices, MappingProxyType):
            object.__setattr__(self, "choices", MappingProxyType(dict(self.choices)))

    def __len__(self) -> int:
        return len(self.choices)

    def __iter__(self):
        return iter(self.choices.items())

    def has(self, section_id: SectionPlanId) -> bool:
        return section_id in self.choices

    def for_section(self, section_id: SectionPlanId) -> VariantChoice | None:
        return self.choices.get(section_id)
