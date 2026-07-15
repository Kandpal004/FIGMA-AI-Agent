"""Component variant and state value objects — atomic-design readiness.

A :class:`Variant` names a purposeful variation of a component (e.g. a Product Card's "compact"
vs "detailed" variant); a :class:`ComponentState` names a UI state it must handle (loading,
empty, error, …). These make the component ready for a design system without prescribing how
any variant or state renders.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.value_objects import ComponentStateKind

__all__ = ["ComponentState", "InvalidVariantError", "Variant"]


class InvalidVariantError(DesignDirectorError):
    """Raised when a variant or state is constructed with invalid data."""

    code = "invalid_component_intelligence_variant"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Variant:
    """A purposeful variation of a component.

    Attributes:
        name: The variant name.
        purpose: Why the variant exists (when to use it).
    """

    name: str
    purpose: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidVariantError("Variant.name must be non-empty.")


@dataclass(frozen=True, slots=True)
class ComponentState:
    """A UI state a component must handle.

    Attributes:
        kind: The state kind.
        description: What the state means for this component.
    """

    kind: ComponentStateKind
    description: str = ""
