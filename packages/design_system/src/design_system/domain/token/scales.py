"""Token scales — the systematic families that make a design system coherent.

Where :mod:`token` models individual tokens, these value objects model the *systems* they form:
a typography scale generated from a base size and a modular ratio, a spacing scale on a grid
step, radius/elevation/shadow/border scales. Each scale names the ordered token keys that make
it up, so the constraint builder can enforce "use the scale, not an arbitrary value" and the
graph builder can wire derivation edges.

A scale never holds literal values itself — it references tokens by key. The tokens hold the
literals; the scale records the *relationship* between them (the ratio, the base step, the
ordered rungs). This keeps the systematic intent auditable and platform-independent.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_system.domain.shared.value_objects import Ratio

__all__ = [
    "BorderScale",
    "ElevationScale",
    "InvalidScaleError",
    "RadiusScale",
    "ShadowScale",
    "SpacingScale",
    "TypographyScale",
]


class InvalidScaleError(DesignDirectorError):
    """Raised when a token scale is constructed with invalid data."""

    code = "invalid_design_system_scale"
    http_status = 422


def _ordered_unique(steps: tuple[str, ...], what: str) -> tuple[str, ...]:
    cleaned = tuple(s.strip().lower() for s in steps if s and s.strip())
    if not cleaned:
        raise InvalidScaleError(f"{what} must name at least one token step.")
    if len(set(cleaned)) != len(cleaned):
        raise InvalidScaleError(f"{what} steps must be unique.", details={"steps": list(cleaned)})
    return cleaned


@dataclass(frozen=True, slots=True)
class TypographyScale:
    """A modular type scale generated from a base size and a ratio.

    Attributes:
        base_px: The base font size in pixels (the ``1.0`` rung).
        ratio: The modular ratio between adjacent rungs (e.g. 1.25 = major third).
        role_tokens: The ordered semantic type-role token keys, small to large
            (e.g. ``("type.caption", "type.body", "type.h3", "type.h2", "type.h1")``).
    """

    base_px: float
    ratio: Ratio
    role_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.base_px > 0:
            raise InvalidScaleError(
                "TypographyScale.base_px must be positive.", details={"base_px": self.base_px}
            )
        object.__setattr__(
            self, "role_tokens", _ordered_unique(self.role_tokens, "TypographyScale")
        )

    @property
    def rungs(self) -> int:
        return len(self.role_tokens)


@dataclass(frozen=True, slots=True)
class SpacingScale:
    """A spacing scale on a fixed grid step.

    Attributes:
        base_px: The grid unit in pixels (every step is a multiple of this).
        step_tokens: The ordered spacing token keys, smallest to largest
            (e.g. ``("space.1", "space.2", "space.4", "space.6", "space.8")``).
    """

    base_px: float
    step_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.base_px > 0:
            raise InvalidScaleError(
                "SpacingScale.base_px must be positive.", details={"base_px": self.base_px}
            )
        object.__setattr__(self, "step_tokens", _ordered_unique(self.step_tokens, "SpacingScale"))

    @property
    def steps(self) -> int:
        return len(self.step_tokens)


@dataclass(frozen=True, slots=True)
class RadiusScale:
    """A corner-radius scale.

    Attributes:
        step_tokens: The ordered radius token keys, smallest to largest
            (e.g. ``("radius.none", "radius.sm", "radius.md", "radius.lg", "radius.full")``).
    """

    step_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_tokens", _ordered_unique(self.step_tokens, "RadiusScale"))


@dataclass(frozen=True, slots=True)
class ElevationScale:
    """A z-elevation scale (surfaces layered by depth).

    Attributes:
        level_tokens: The ordered elevation token keys, lowest to highest
            (e.g. ``("elevation.0", "elevation.1", "elevation.2", "elevation.3")``).
    """

    level_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "level_tokens", _ordered_unique(self.level_tokens, "ElevationScale")
        )


@dataclass(frozen=True, slots=True)
class ShadowScale:
    """A shadow scale (the visual expression of elevation).

    Attributes:
        step_tokens: The ordered shadow token keys, softest to strongest
            (e.g. ``("shadow.sm", "shadow.md", "shadow.lg")``).
    """

    step_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_tokens", _ordered_unique(self.step_tokens, "ShadowScale"))


@dataclass(frozen=True, slots=True)
class BorderScale:
    """A border-width scale.

    Attributes:
        width_tokens: The ordered border-width token keys, thinnest to thickest
            (e.g. ``("border.0", "border.1", "border.2")``).
    """

    width_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "width_tokens", _ordered_unique(self.width_tokens, "BorderScale")
        )
