"""Geometry value objects — token-first sizing, spacing, and radius.

Where a naive Figma model would carry raw pixel numbers, this engine keeps geometry
*token-first*: a :class:`Size` is a sizing mode (HUG/FILL/FIXED) with a pixel value only when
FIXED; :class:`Padding` and :class:`CornerRadius` reference Design-System spacing/radius variable
keys rather than literals, so a downstream renderer binds Figma variables instead of hard-coding.
This mirrors how a senior designer builds a variable-driven file.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.shared.value_objects import SizingMode

__all__ = ["CornerRadius", "InvalidGeometryError", "Padding", "Size"]

_TOKEN_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidGeometryError(DesignDirectorError):
    """Raised when a geometry value object is constructed with invalid data."""

    code = "invalid_figma_design_geometry"
    http_status = 422


def _token_key(key: str, what: str) -> str:
    normalized = key.strip().lower()
    if not _TOKEN_KEY.match(normalized):
        raise InvalidGeometryError(
            f"{what} must reference a dotted token key; got {key!r}.", details={"key": key}
        )
    return normalized


@dataclass(frozen=True, slots=True)
class Size:
    """How a node sizes along one axis.

    Attributes:
        mode: The sizing mode (fixed / hug / fill).
        px: The pixel value — required for FIXED, forbidden otherwise.
    """

    mode: SizingMode
    px: float | None = None

    def __post_init__(self) -> None:
        if self.mode is SizingMode.FIXED:
            if self.px is None or self.px < 0:
                raise InvalidGeometryError(
                    "A FIXED size requires a non-negative pixel value.",
                    details={"px": self.px},
                )
        elif self.px is not None:
            raise InvalidGeometryError(
                "Only a FIXED size may carry a pixel value.", details={"mode": self.mode.value}
            )

    @classmethod
    def fixed(cls, px: float) -> Size:
        return cls(mode=SizingMode.FIXED, px=px)

    @classmethod
    def hug(cls) -> Size:
        return cls(mode=SizingMode.HUG)

    @classmethod
    def fill(cls) -> Size:
        return cls(mode=SizingMode.FILL)


@dataclass(frozen=True, slots=True)
class Padding:
    """The four-sided padding of an auto-layout frame, as spacing variable keys.

    Attributes:
        top: The spacing token key for top padding.
        right: The spacing token key for right padding.
        bottom: The spacing token key for bottom padding.
        left: The spacing token key for left padding.
    """

    top: str
    right: str
    bottom: str
    left: str

    def __post_init__(self) -> None:
        for name in ("top", "right", "bottom", "left"):
            object.__setattr__(self, name, _token_key(getattr(self, name), f"Padding.{name}"))

    @classmethod
    def uniform(cls, token: str) -> Padding:
        return cls(top=token, right=token, bottom=token, left=token)

    @classmethod
    def symmetric(cls, vertical: str, horizontal: str) -> Padding:
        return cls(top=vertical, right=horizontal, bottom=vertical, left=horizontal)

    @property
    def token_keys(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.top, self.right, self.bottom, self.left)))


@dataclass(frozen=True, slots=True)
class CornerRadius:
    """A corner radius, as a radius variable key.

    Attributes:
        token: The radius token key.
    """

    token: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "token", _token_key(self.token, "CornerRadius.token"))
