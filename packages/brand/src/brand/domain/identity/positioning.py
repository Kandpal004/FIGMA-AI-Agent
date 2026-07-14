"""Brand positioning — the space the brand owns in the customer's mind.

A :class:`BrandPositioning` is the brand-level counterpart to the business positioning
it derives from: the frame of reference, the point of difference, and the reason to
believe, expressed as brand identity rather than commercial strategy. Cited and
singular per report.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import Confidence, ConsideredAlternative

__all__ = ["BrandPositioning", "InvalidPositioningError"]


class InvalidPositioningError(DesignDirectorError):
    """Raised when brand positioning is constructed with invalid data."""

    code = "invalid_brand_positioning"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandPositioning:
    """The cited space the brand owns.

    Attributes:
        statement: The one-line positioning statement.
        frame_of_reference: The category/context the brand competes in.
        point_of_difference: What sets the brand apart.
        reason_to_believe: Why the difference is credible.
        confidence: Confidence in the positioning.
        considered: Positions weighed and rejected.
        evidence_ids: The evidence supporting it.
    """

    statement: str
    frame_of_reference: str
    point_of_difference: str
    reason_to_believe: str = ""
    confidence: Confidence = Confidence(0.7)
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("statement", "frame_of_reference", "point_of_difference"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise InvalidPositioningError(f"BrandPositioning.{name} must be non-empty.")
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
