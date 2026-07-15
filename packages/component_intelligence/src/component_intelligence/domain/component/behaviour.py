"""Component behaviour value objects — how a component behaves, not how it looks.

These capture a component's mobile behaviour, its per-breakpoint responsive rules, its
interaction rules, and its animation rules — all as intent, never as a visual or code
specification. The downstream Design System implements them; the engine decides them.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.value_objects import (
    AnimationKind,
    Breakpoint,
    InteractionKind,
    ResponsiveIntent,
)

__all__ = [
    "AnimationRule",
    "InteractionRule",
    "InvalidBehaviourError",
    "MobileBehaviour",
    "ResponsiveRule",
]


class InvalidBehaviourError(DesignDirectorError):
    """Raised when a behaviour value object is constructed with invalid data."""

    code = "invalid_component_intelligence_behaviour"
    http_status = 422


@dataclass(frozen=True, slots=True)
class MobileBehaviour:
    """How a component behaves on mobile.

    Attributes:
        intent: The mobile posture (e.g. "collapse to a drawer", "become a sticky bar").
    """

    intent: str

    def __post_init__(self) -> None:
        if not self.intent or not self.intent.strip():
            raise InvalidBehaviourError("MobileBehaviour.intent must be non-empty.")


@dataclass(frozen=True, slots=True)
class ResponsiveRule:
    """How a component behaves at one breakpoint."""

    breakpoint: Breakpoint
    intent: ResponsiveIntent


@dataclass(frozen=True, slots=True)
class InteractionRule:
    """An interaction behaviour a component requires.

    Attributes:
        kind: The interaction kind.
        intent: What the interaction accomplishes.
    """

    kind: InteractionKind
    intent: str = ""


@dataclass(frozen=True, slots=True)
class AnimationRule:
    """A restrained animation a component may use.

    Attributes:
        kind: The animation posture.
        intent: What the animation reinforces (never decoration).
    """

    kind: AnimationKind
    intent: str = ""
