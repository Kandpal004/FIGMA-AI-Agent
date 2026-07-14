"""Typography direction — strategic intent for type (never fonts or sizes).

A :class:`TypographyDirection` chooses the typographic *voices* for display and body
and states the hierarchy intent — it names no font files, sizes, or line-heights (that
is a later phase). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import TypeVoice

__all__ = ["InvalidTypographyError", "TypographyDirection"]


class InvalidTypographyError(DesignDirectorError):
    """Raised when typography direction is constructed with invalid data."""

    code = "invalid_typography_direction"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TypographyDirection:
    """The cited strategic intent for typography.

    Attributes:
        display_voice: The typographic voice for headings/display.
        body_voice: The typographic voice for body text.
        hierarchy_intent: How type hierarchy should feel (e.g. "high contrast, editorial").
        rationale: Why these voices express the brand.
        principles: Typographic principles to honour.
        evidence_ids: The evidence supporting it.
    """

    display_voice: TypeVoice
    body_voice: TypeVoice
    hierarchy_intent: str = ""
    rationale: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
