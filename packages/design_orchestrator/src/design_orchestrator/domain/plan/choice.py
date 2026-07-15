"""The choices a section plan commits to — layout, spacing, typography, visual language.

The orchestrator does not invent visual values; it *chooses* from what the Design System (P16)
already declared. Each of these value objects therefore records a decision expressed in terms of
Design-System token keys and enumerated modes, never literals:

* :class:`LayoutRule` — how a section arranges its content (mode, alignment, density, columns).
* :class:`SpacingRule` — which spacing-scale token steps set the rhythm.
* :class:`TypographyChoice` — which semantic type-role token the section leads with.
* :class:`VisualChoice` — the theme mode, the surface token, and the emphasis level.

Every token key referenced here is validated against the live Design System by the selection
resolver (application layer); the domain guarantees each choice is internally well-formed.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.value_objects import (
    Alignment,
    Density,
    LayoutMode,
    ThemeMode,
)

__all__ = [
    "InvalidChoiceError",
    "LayoutRule",
    "SpacingRule",
    "TypographyChoice",
    "VisualChoice",
]

# A dotted, lower-case Design-System token key: ``space.4``, ``type.h1``, ``color.bg.default``.
_TOKEN_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidChoiceError(DesignDirectorError):
    """Raised when a section choice is constructed with invalid data."""

    code = "invalid_design_orchestrator_choice"
    http_status = 422


def _token_key(key: str, what: str) -> str:
    normalized = key.strip().lower()
    if not _TOKEN_KEY.match(normalized):
        raise InvalidChoiceError(
            f"{what} must reference a dotted token key (e.g. 'space.4'); got {key!r}.",
            details={"key": key},
        )
    return normalized


def _token_keys(keys, what: str) -> tuple[str, ...]:
    cleaned = tuple(_token_key(k, what) for k in keys if k and k.strip())
    if not cleaned:
        raise InvalidChoiceError(f"{what} must reference at least one token.")
    if len(set(cleaned)) != len(cleaned):
        raise InvalidChoiceError(f"{what} token keys must be unique.")
    return cleaned


@dataclass(frozen=True, slots=True)
class LayoutRule:
    """How a section arranges its content.

    Attributes:
        mode: The layout mode (stack / grid / split / full-bleed).
        alignment: Content alignment.
        density: Spacing density.
        columns: Column count for a grid layout (>= 1; 1 for non-grid modes).
    """

    mode: LayoutMode
    alignment: Alignment = Alignment.START
    density: Density = Density.REGULAR
    columns: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.columns, int) or isinstance(self.columns, bool):
            raise InvalidChoiceError("LayoutRule.columns must be an int.")
        if self.columns < 1:
            raise InvalidChoiceError(
                "LayoutRule.columns must be >= 1.", details={"columns": self.columns}
            )
        if self.mode is LayoutMode.GRID and self.columns < 2:
            raise InvalidChoiceError("A grid layout must use at least two columns.")


@dataclass(frozen=True, slots=True)
class SpacingRule:
    """Which spacing-scale token steps set a section's rhythm.

    Attributes:
        gap_token: The spacing token used between items.
        block_token: The spacing token used above/below the section.
    """

    gap_token: str
    block_token: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_token", _token_key(self.gap_token, "SpacingRule.gap_token"))
        object.__setattr__(
            self, "block_token", _token_key(self.block_token, "SpacingRule.block_token")
        )

    @property
    def token_keys(self) -> tuple[str, ...]:
        return (self.gap_token, self.block_token)


@dataclass(frozen=True, slots=True)
class TypographyChoice:
    """Which semantic type-role token a section leads with.

    Attributes:
        heading_token: The type-role token for the section heading.
        body_token: The type-role token for the section body.
    """

    heading_token: str
    body_token: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "heading_token", _token_key(self.heading_token, "TypographyChoice.heading_token")
        )
        object.__setattr__(
            self, "body_token", _token_key(self.body_token, "TypographyChoice.body_token")
        )

    @property
    def token_keys(self) -> tuple[str, ...]:
        return (self.heading_token, self.body_token)


@dataclass(frozen=True, slots=True)
class VisualChoice:
    """The theme mode, surface token, and emphasis of a section's visual language.

    Attributes:
        theme_mode: The theme mode the section targets by default.
        surface_tokens: The surface/background token(s) the section sits on.
        emphasis: A 1–3 emphasis level (3 = hero-level prominence).
    """

    theme_mode: ThemeMode
    surface_tokens: tuple[str, ...]
    emphasis: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "surface_tokens", _token_keys(self.surface_tokens, "VisualChoice.surface_tokens")
        )
        if not isinstance(self.emphasis, int) or isinstance(self.emphasis, bool):
            raise InvalidChoiceError("VisualChoice.emphasis must be an int.")
        if not 1 <= self.emphasis <= 3:
            raise InvalidChoiceError(
                "VisualChoice.emphasis must be within [1, 3].",
                details={"emphasis": self.emphasis},
            )
