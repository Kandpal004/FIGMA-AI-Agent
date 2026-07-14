"""Color philosophy — strategic intent for colour (never hex values).

A :class:`ColorPhilosophy` states the temperament, contrast register, and the *meaning*
colour must carry — the role of the accent, what neutrals do, what colour should never
do. It names no hex values, palettes, or tokens (that is a later phase). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import ColorTemperament, ContrastLevel

__all__ = ["ColorPhilosophy", "InvalidColorError"]


class InvalidColorError(DesignDirectorError):
    """Raised when colour philosophy is constructed with invalid data."""

    code = "invalid_color_philosophy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ColorPhilosophy:
    """The cited strategic intent for colour.

    Attributes:
        temperament: The overall colour temperature.
        contrast: The contrast register.
        accent_role: What the accent colour is reserved for (e.g. "action and trust").
        neutrals_role: What neutrals carry (e.g. "calm, editorial base").
        meaning: The meaning colour must convey.
        avoid: What colour must never do.
        evidence_ids: The evidence supporting it.
    """

    temperament: ColorTemperament
    contrast: ContrastLevel
    accent_role: str = ""
    neutrals_role: str = ""
    meaning: str = ""
    avoid: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "avoid", tuple(self.avoid))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
