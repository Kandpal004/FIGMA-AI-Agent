"""Localization — the direction and locale contract the design system guarantees.

A :class:`Localization` records which text directions the system supports and which semantic
token keys and properties must *mirror* under RTL (padding-inline, float, chevron direction,
…), plus the locales in scope. When RTL is supported, the constraint builder emits an
``RTL_MIRROR`` constraint and the design system guarantees every mirrored token has a logical
(direction-aware) counterpart, so a future UI cannot ship an LTR-only layout by accident.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_system.domain.shared.value_objects import Direction

__all__ = ["InvalidLocalizationError", "Localization"]


class InvalidLocalizationError(DesignDirectorError):
    """Raised when localization data is constructed with invalid data."""

    code = "invalid_design_system_localization"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Localization:
    """The direction/locale contract the system supports.

    Attributes:
        directions: The supported text directions (LTR always present; RTL when required).
        locales: The supported locale tags, primary first (e.g. ``("en", "ar")``).
        mirror_properties: The logical properties that must mirror under RTL (e.g.
            ``("padding-inline-start", "margin-inline-end", "text-align")``). Required and
            non-empty when RTL is supported; must be empty otherwise.
    """

    directions: tuple[Direction, ...] = (Direction.LTR,)
    locales: tuple[str, ...] = ("en",)
    mirror_properties: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        directions = tuple(dict.fromkeys(self.directions))
        if Direction.LTR not in directions:
            directions = (Direction.LTR, *directions)
        locales = tuple(
            dict.fromkeys(loc.strip().lower() for loc in self.locales if loc and loc.strip())
        )
        if not locales:
            locales = ("en",)
        mirror = tuple(
            dict.fromkeys(p.strip().lower() for p in self.mirror_properties if p and p.strip())
        )
        if Direction.RTL in directions and not mirror:
            raise InvalidLocalizationError(
                "RTL support requires at least one mirror property."
            )
        if Direction.RTL not in directions and mirror:
            raise InvalidLocalizationError(
                "Mirror properties are only meaningful when RTL is supported."
            )
        object.__setattr__(self, "directions", directions)
        object.__setattr__(self, "locales", locales)
        object.__setattr__(self, "mirror_properties", mirror)

    @property
    def supports_rtl(self) -> bool:
        return Direction.RTL in self.directions

    @property
    def primary_locale(self) -> str:
        return self.locales[0]
