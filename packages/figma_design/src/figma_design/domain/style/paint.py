"""Paint and Effect value objects — the visual fills and effects a style carries.

A :class:`Paint` is a fill: a solid colour, a gradient, or an image. An :class:`Effect` is a
shadow or blur. Both are token-first where it matters — a solid paint references a colour variable
key rather than a raw hex, so the published style binds a Figma variable and the file stays
DRY.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.shared.value_objects import BlendMode, EffectType, PaintType

__all__ = ["Effect", "InvalidPaintError", "Paint"]

_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidPaintError(DesignDirectorError):
    """Raised when a paint or effect is constructed with invalid data."""

    code = "invalid_figma_design_paint"
    http_status = 422


def _key(value: str, what: str) -> str:
    normalized = value.strip().lower()
    if not _KEY.match(normalized):
        raise InvalidPaintError(
            f"{what} must reference a dotted token key; got {value!r}.", details={"value": value}
        )
    return normalized


@dataclass(frozen=True, slots=True)
class Paint:
    """A fill.

    Attributes:
        type: The paint type (solid / gradient / image).
        color_token: The colour variable key for a SOLID paint (required for SOLID, else empty).
        opacity: The paint opacity in ``[0, 1]``.
        blend_mode: The blend mode.
        image_ref: An opaque image reference for an IMAGE paint (required for IMAGE, else empty).
    """

    type: PaintType
    color_token: str = ""
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    image_ref: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.opacity <= 1.0:
            raise InvalidPaintError("Paint.opacity must be within [0, 1].")
        if self.type is PaintType.SOLID:
            if not self.color_token:
                raise InvalidPaintError("A SOLID paint requires a colour token.")
            object.__setattr__(self, "color_token", _key(self.color_token, "Paint.color_token"))
        elif self.type is PaintType.IMAGE:
            if not self.image_ref or not self.image_ref.strip():
                raise InvalidPaintError("An IMAGE paint requires an image_ref.")
            object.__setattr__(self, "image_ref", self.image_ref.strip())
        elif self.color_token:
            object.__setattr__(self, "color_token", _key(self.color_token, "Paint.color_token"))

    @property
    def token_keys(self) -> tuple[str, ...]:
        return (self.color_token,) if self.color_token else ()


@dataclass(frozen=True, slots=True)
class Effect:
    """A shadow or blur effect.

    Attributes:
        type: The effect type (drop/inner shadow, layer/background blur).
        radius: The blur radius in pixels.
        color_token: The colour variable key for a shadow (required for shadows, else empty).
        offset_x: The shadow x offset (shadows only).
        offset_y: The shadow y offset (shadows only).
    """

    type: EffectType
    radius: float
    color_token: str = ""
    offset_x: float = 0.0
    offset_y: float = 0.0

    def __post_init__(self) -> None:
        if self.radius < 0:
            raise InvalidPaintError("Effect.radius must be non-negative.")
        is_shadow = self.type in (EffectType.DROP_SHADOW, EffectType.INNER_SHADOW)
        if is_shadow:
            if not self.color_token:
                raise InvalidPaintError("A shadow effect requires a colour token.")
            object.__setattr__(self, "color_token", _key(self.color_token, "Effect.color_token"))
        elif self.color_token:
            object.__setattr__(self, "color_token", _key(self.color_token, "Effect.color_token"))

    @property
    def token_keys(self) -> tuple[str, ...]:
        return (self.color_token,) if self.color_token else ()
