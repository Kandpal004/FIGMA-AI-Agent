"""Iconography direction — strategic intent for icons (never an icon set).

An :class:`IconographyDirection` states the icon style and principles the system must
follow — it draws no icons and names no icon library (that is a later phase). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import IconStyle

__all__ = ["IconographyDirection", "InvalidIconographyError"]


class InvalidIconographyError(DesignDirectorError):
    """Raised when iconography direction is constructed with invalid data."""

    code = "invalid_iconography_direction"
    http_status = 422


@dataclass(frozen=True, slots=True)
class IconographyDirection:
    """The cited strategic intent for iconography.

    Attributes:
        style: The icon style.
        weight_intent: How heavy/light icons should feel.
        principles: Iconography principles to honour.
        evidence_ids: The evidence supporting it.
    """

    style: IconStyle
    weight_intent: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
