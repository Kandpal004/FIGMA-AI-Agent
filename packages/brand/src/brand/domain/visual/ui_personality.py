"""UI & component personality — how the interface should *feel*.

:class:`UIPersonality` states the interface's overall feel (corner language, weight,
density, texture), and :class:`ComponentPersonality` states how individual components
(buttons, cards, inputs) should feel. These are the keystones every downstream
component and token decision must express — they specify no CSS, tokens, or code.
Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import (
    ComponentWeight,
    CornerLanguage,
    SpacingDensity,
    UITexture,
)

__all__ = ["ComponentPersonality", "InvalidUIPersonalityError", "UIPersonality"]


class InvalidUIPersonalityError(DesignDirectorError):
    """Raised when UI/component personality is constructed with invalid data."""

    code = "invalid_ui_personality"
    http_status = 422


@dataclass(frozen=True, slots=True)
class UIPersonality:
    """The cited strategic intent for how the interface should feel.

    Attributes:
        corner_language: The corner treatment.
        weight: The overall visual weight.
        density: The spatial density of the interface.
        texture: The texture/depth the interface expresses.
        feel: A one-line description of the intended feel.
        principles: UI-feel principles to honour.
        evidence_ids: The evidence supporting it.
    """

    corner_language: CornerLanguage
    weight: ComponentWeight
    density: SpacingDensity
    texture: UITexture
    feel: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ComponentPersonality:
    """The cited strategic intent for how components should feel.

    Attributes:
        interaction_feel: How interactions should feel (e.g. "crisp, immediate").
        emphasis: How primary actions should carry emphasis.
        restraint: What components should never do.
        principles: Component-feel principles to honour.
        evidence_ids: The evidence supporting it.
    """

    interaction_feel: str = ""
    emphasis: str = ""
    restraint: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
