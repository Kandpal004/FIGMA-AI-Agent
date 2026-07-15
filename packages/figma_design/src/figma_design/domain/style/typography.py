"""The Typography style model — a text style's type properties.

A :class:`TypographyStyle` captures the properties a Figma text style carries: font family, weight,
and size/line-height/letter-spacing that reference type-scale variable keys. It is the type half
of the published style library, built from the Design System's typography scale.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

__all__ = ["InvalidTypographyError", "TypographyStyle"]

_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidTypographyError(DesignDirectorError):
    """Raised when a typography style is constructed with invalid data."""

    code = "invalid_figma_design_typography"
    http_status = 422


def _key(value: str, what: str) -> str:
    normalized = value.strip().lower()
    if not _KEY.match(normalized):
        raise InvalidTypographyError(
            f"{what} must reference a dotted token key; got {value!r}.", details={"value": value}
        )
    return normalized


@dataclass(frozen=True, slots=True)
class TypographyStyle:
    """A text style's type properties.

    Attributes:
        font_family: The font family name.
        font_weight: The numeric font weight (100–900).
        font_size_token: The type-size variable key.
        line_height: The line height as a unit-less multiplier (e.g. 1.4).
        letter_spacing: The letter spacing in ems.
        text_case: The text case ("none", "upper", "lower", "title").
    """

    font_family: str
    font_weight: int
    font_size_token: str
    line_height: float = 1.4
    letter_spacing: float = 0.0
    text_case: str = "none"

    def __post_init__(self) -> None:
        if not self.font_family or not self.font_family.strip():
            raise InvalidTypographyError("TypographyStyle.font_family must be non-empty.")
        if not 100 <= self.font_weight <= 900:
            raise InvalidTypographyError("TypographyStyle.font_weight must be within [100, 900].")
        if not self.line_height > 0:
            raise InvalidTypographyError("TypographyStyle.line_height must be positive.")
        if self.text_case not in ("none", "upper", "lower", "title"):
            raise InvalidTypographyError(
                "TypographyStyle.text_case must be none/upper/lower/title.",
                details={"text_case": self.text_case},
            )
        object.__setattr__(self, "font_family", self.font_family.strip())
        object.__setattr__(
            self, "font_size_token", _key(self.font_size_token, "TypographyStyle.font_size_token")
        )

    @property
    def token_keys(self) -> tuple[str, ...]:
        return (self.font_size_token,)
