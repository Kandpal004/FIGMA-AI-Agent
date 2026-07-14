"""Spacing philosophy — strategic intent for space (never pixels or scales).

A :class:`SpacingPhilosophy` states the spatial density and rhythm the brand's layouts
should feel like — generosity vs efficiency, the role of whitespace. It names no
pixel values or spacing scales (that is a later phase). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import SpacingDensity

__all__ = ["InvalidSpacingError", "SpacingPhilosophy"]


class InvalidSpacingError(DesignDirectorError):
    """Raised when spacing philosophy is constructed with invalid data."""

    code = "invalid_spacing_philosophy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SpacingPhilosophy:
    """The cited strategic intent for space.

    Attributes:
        density: The spatial density the layout should feel.
        rhythm_intent: How spatial rhythm should feel (e.g. "generous, unhurried").
        whitespace_role: What whitespace communicates for this brand.
        principles: Spatial principles to honour.
        evidence_ids: The evidence supporting it.
    """

    density: SpacingDensity
    rhythm_intent: str = ""
    whitespace_role: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
