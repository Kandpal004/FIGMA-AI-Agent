"""Abstract token scales — the systematic ramps the language defines, without values.

These value objects define the *structure* of the token system: how many steps a spacing or
type ramp has, the modular base and ratio they follow, how many elevation and radius levels
exist, the motion timing tiers, and the contrast targets. They are relative, unitless
definitions — an "8-unit base, 1.25 ratio, 7 steps" is a language decision, not a pixel. The
downstream Design System materialises them into concrete values.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.value_objects import Ratio

__all__ = [
    "ContrastTargets",
    "ElevationScale",
    "InvalidScaleError",
    "MotionTokens",
    "RadiusScale",
    "SpacingScale",
    "TypeScale",
]


class InvalidScaleError(DesignDirectorError):
    """Raised when a token scale is constructed with invalid data."""

    code = "invalid_design_language_scale"
    http_status = 422


def _positive(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidScaleError(f"{name} must be a positive int.", details={"value": value})
    return value


@dataclass(frozen=True, slots=True)
class SpacingScale:
    """A modular spacing ramp (relative base, no pixels).

    Attributes:
        base_unit: The modular base (e.g. 4 or 8), unitless.
        ratio: The step multiplier between spacing sizes.
        steps: How many spacing steps the ramp defines.
    """

    base_unit: int = 8
    ratio: Ratio = Ratio(1.5)
    steps: int = 8

    def __post_init__(self) -> None:
        _positive("SpacingScale.base_unit", self.base_unit)
        _positive("SpacingScale.steps", self.steps)


@dataclass(frozen=True, slots=True)
class TypeScale:
    """A modular type ramp.

    Attributes:
        ratio: The modular ratio between type sizes (e.g. 1.25).
        steps: How many type sizes the ramp defines.
    """

    ratio: Ratio = Ratio(1.25)
    steps: int = 7

    def __post_init__(self) -> None:
        _positive("TypeScale.steps", self.steps)


@dataclass(frozen=True, slots=True)
class RadiusScale:
    """A corner-radius ramp.

    Attributes:
        steps: How many radius steps the ramp defines.
        sharpness: The posture ("sharp", "soft", "rounded", "pill").
    """

    steps: int = 4
    sharpness: str = "soft"

    def __post_init__(self) -> None:
        _positive("RadiusScale.steps", self.steps)
        if not self.sharpness.strip():
            raise InvalidScaleError("RadiusScale.sharpness must be non-empty.")


@dataclass(frozen=True, slots=True)
class ElevationScale:
    """A shadow/elevation ramp.

    Attributes:
        levels: How many elevation levels exist (0 = flat).
        posture: The posture ("flat", "subtle", "layered", "pronounced").
    """

    levels: int = 3
    posture: str = "subtle"

    def __post_init__(self) -> None:
        if not isinstance(self.levels, int) or isinstance(self.levels, bool) or self.levels < 0:
            raise InvalidScaleError(
                "ElevationScale.levels must be a non-negative int.", details={"value": self.levels}
            )
        if not self.posture.strip():
            raise InvalidScaleError("ElevationScale.posture must be non-empty.")


@dataclass(frozen=True, slots=True)
class MotionTokens:
    """Motion timing tiers (relative, no concrete milliseconds mandated).

    Attributes:
        duration_tiers: How many duration tiers exist (e.g. fast/base/slow).
        easing: The easing posture ("linear", "standard", "expressive", "restrained").
    """

    duration_tiers: int = 3
    easing: str = "restrained"

    def __post_init__(self) -> None:
        _positive("MotionTokens.duration_tiers", self.duration_tiers)
        if not self.easing.strip():
            raise InvalidScaleError("MotionTokens.easing must be non-empty.")


@dataclass(frozen=True, slots=True)
class ContrastTargets:
    """The contrast the language commits to (WCAG-aligned intent, not concrete colours).

    Attributes:
        text_min: The minimum text contrast ratio target (e.g. 4.5).
        ui_min: The minimum non-text/UI contrast ratio target (e.g. 3.0).
    """

    text_min: float = 4.5
    ui_min: float = 3.0

    def __post_init__(self) -> None:
        if self.text_min < 1.0 or self.ui_min < 1.0:
            raise InvalidScaleError(
                "ContrastTargets must be >= 1.0 contrast ratios.",
                details={"text_min": self.text_min, "ui_min": self.ui_min},
            )
