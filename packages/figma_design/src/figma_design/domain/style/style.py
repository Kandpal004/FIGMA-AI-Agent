"""The Style model — the published library styles a designer defines once and reuses.

A :class:`Style` is a published paint, text, effect, or grid style. Nodes reference styles by id
rather than repeating paints and type properties, exactly as a senior designer keeps a file DRY:
styles reference variables, nodes reference styles. A :class:`StyleSet` is the immutable,
unique-by-id registry of every published style.

Pure domain: standard library, the shared-kernel error base, FD ids, the paint/typography value
objects, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import StyleId
from figma_design.domain.shared.value_objects import StyleType
from figma_design.domain.style.paint import Effect, Paint
from figma_design.domain.style.typography import TypographyStyle

__all__ = ["InvalidStyleError", "Style", "StyleSet"]


class InvalidStyleError(DesignDirectorError):
    """Raised when a style or style set is constructed with invalid data."""

    code = "invalid_figma_design_style"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Style:
    """One published style.

    Attributes:
        id: Style identity.
        name: The published style name (e.g. "Surface/Default", "Heading/H1").
        type: The style type (fill / text / effect / grid).
        paints: The paints for a FILL style (required, non-empty for FILL).
        typography: The type properties for a TEXT style (required for TEXT).
        effects: The effects for an EFFECT style (required, non-empty for EFFECT).
        grid_columns: The column count for a GRID style (required > 0 for GRID).
        description: Human-readable intent.
    """

    id: StyleId
    name: str
    type: StyleType
    paints: tuple[Paint, ...] = ()
    typography: TypographyStyle | None = None
    effects: tuple[Effect, ...] = ()
    grid_columns: int = 0
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidStyleError("Style.name must be non-empty.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "paints", tuple(self.paints))
        object.__setattr__(self, "effects", tuple(self.effects))
        if self.type is StyleType.FILL and not self.paints:
            raise InvalidStyleError("A FILL style requires at least one paint.")
        if self.type is StyleType.TEXT and self.typography is None:
            raise InvalidStyleError("A TEXT style requires typography.")
        if self.type is StyleType.EFFECT and not self.effects:
            raise InvalidStyleError("An EFFECT style requires at least one effect.")
        if self.type is StyleType.GRID and self.grid_columns <= 0:
            raise InvalidStyleError("A GRID style requires a positive column count.")

    @property
    def token_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        for paint in self.paints:
            keys.extend(paint.token_keys)
        for effect in self.effects:
            keys.extend(effect.token_keys)
        if self.typography is not None:
            keys.extend(self.typography.token_keys)
        return tuple(dict.fromkeys(keys))


@dataclass(frozen=True, slots=True)
class StyleSet:
    """The immutable, unique-by-id registry of published styles."""

    items: Mapping[StyleId, Style] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def of(cls, styles: Iterable[Style]) -> StyleSet:
        mapping: dict[StyleId, Style] = {}
        for style in styles:
            if style.id in mapping:
                raise InvalidStyleError("Duplicate style id.", details={"id": str(style.id)})
            mapping[style.id] = style
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def has(self, style_id: StyleId) -> bool:
        return style_id in self.items

    def get(self, style_id: StyleId) -> Style:
        style = self.items.get(style_id)
        if style is None:
            raise InvalidStyleError(f"Style {style_id} not found.", details={"id": str(style_id)})
        return style

    def by_type(self, style_type: StyleType) -> tuple[Style, ...]:
        return tuple(s for s in self.items.values() if s.type is style_type)
