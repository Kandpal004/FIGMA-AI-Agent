"""Themes — the mode-specific resolution of semantic tokens.

A :class:`Theme` binds a :class:`ThemeMode` (light or dark) to concrete overrides for the
semantic tokens whose value differs by mode — the surfaces, texts, and borders that must invert
between light and dark. A theme never redefines primitives; it remaps *semantic* token keys to
different primitives (light: ``color.text.default`` → ``gray.900``; dark: → ``gray.50``).

A :class:`ThemeSet` is the immutable collection of a specification's themes and enforces
**theme parity**: a design system that ships dark mode must define *both* the light and the dark
theme, and both must remap the same set of semantic keys — no token may be themed in one mode but
forgotten in the other. This makes a half-finished dark mode structurally impossible.

Pure domain: standard library, the shared-kernel error base, DS ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.shared.ids import ThemeId
from design_system.domain.shared.value_objects import ThemeMode

__all__ = ["InvalidThemeError", "Theme", "ThemeSet"]


class InvalidThemeError(DesignDirectorError):
    """Raised when a theme or theme set violates a structural invariant."""

    code = "invalid_design_system_theme"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Theme:
    """A mode-specific remapping of semantic tokens to primitives.

    Attributes:
        id: Theme identity within this specification.
        mode: The theme mode (light or dark).
        name: A human-readable theme name.
        overrides: The semantic-token-key → primitive-token-key remapping for this mode. Must be
            non-empty.
    """

    id: ThemeId
    mode: ThemeMode
    name: str
    overrides: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidThemeError("Theme.name must be non-empty.")
        overrides = {
            k.strip().lower(): v.strip().lower()
            for k, v in self.overrides.items()
            if k and k.strip() and v and v.strip()
        }
        if not overrides:
            raise InvalidThemeError(
                "A Theme must remap at least one semantic token.",
                details={"mode": self.mode.value},
            )
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "overrides", MappingProxyType(overrides))

    @property
    def themed_keys(self) -> frozenset[str]:
        return frozenset(self.overrides.keys())


@dataclass(frozen=True, slots=True)
class ThemeSet:
    """The immutable set of a specification's themes, keyed by mode.

    Enforces theme parity: when more than one mode is present, every mode must theme exactly the
    same set of semantic keys.
    """

    items: Mapping[ThemeMode, Theme] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        data = dict(self.items)
        if not data:
            raise InvalidThemeError("A ThemeSet must contain at least the light theme.")
        for mode, theme in data.items():
            if theme.mode is not mode:
                raise InvalidThemeError(
                    "Theme key must match its mode.",
                    details={"key": mode.value, "theme": theme.mode.value},
                )
        if ThemeMode.LIGHT not in data:
            raise InvalidThemeError("A ThemeSet must define the light theme.")
        keysets = {mode: theme.themed_keys for mode, theme in data.items()}
        baseline = keysets[ThemeMode.LIGHT]
        for mode, keys in keysets.items():
            if keys != baseline:
                raise InvalidThemeError(
                    "Theme parity violated: modes must theme the same semantic keys.",
                    details={
                        "mode": mode.value,
                        "missing": sorted(baseline - keys),
                        "extra": sorted(keys - baseline),
                    },
                )
        object.__setattr__(self, "items", MappingProxyType(data))

    @classmethod
    def of(cls, themes: Iterable[Theme]) -> ThemeSet:
        mapping: dict[ThemeMode, Theme] = {}
        for theme in themes:
            if theme.mode in mapping:
                raise InvalidThemeError(
                    "Duplicate theme mode.", details={"mode": theme.mode.value}
                )
            mapping[theme.mode] = theme
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    @property
    def modes(self) -> tuple[ThemeMode, ...]:
        return tuple(self.items.keys())

    @property
    def has_dark(self) -> bool:
        return ThemeMode.DARK in self.items

    def get(self, mode: ThemeMode) -> Theme:
        theme = self.items.get(mode)
        if theme is None:
            raise InvalidThemeError(f"No {mode.value} theme.", details={"mode": mode.value})
        return theme
