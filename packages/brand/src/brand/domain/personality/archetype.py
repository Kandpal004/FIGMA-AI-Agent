"""Brand archetype — the timeless character the brand embodies.

An :class:`ArchetypeBlend` names a primary :class:`BrandArchetype` and an optional
secondary with a blend weight — most strong brands are a dominant archetype with a
supporting note (a Sage with Hero energy, a Lover with Creator flair). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import (
    BrandArchetype,
    ConsideredAlternative,
    Percentage,
)

__all__ = ["ArchetypeBlend", "InvalidArchetypeError"]


class InvalidArchetypeError(DesignDirectorError):
    """Raised when an archetype blend is constructed with invalid data."""

    code = "invalid_brand_archetype"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ArchetypeBlend:
    """The cited archetype the brand embodies.

    Attributes:
        primary: The dominant archetype.
        primary_weight: How dominant the primary is (``[0.5, 1]``).
        secondary: An optional supporting archetype.
        rationale: Why this archetype fits the brand.
        considered: Archetypes weighed and rejected.
        evidence_ids: The evidence supporting it.
    """

    primary: BrandArchetype
    primary_weight: Percentage = Percentage(0.7)
    secondary: BrandArchetype | None = None
    rationale: str = ""
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.secondary is self.primary:
            raise InvalidArchetypeError(
                "ArchetypeBlend.secondary must differ from the primary.",
                details={"archetype": self.primary.value},
            )
        if self.primary_weight.value < 0.5:
            raise InvalidArchetypeError(
                "ArchetypeBlend.primary_weight must be >= 0.5 (the primary must dominate).",
                details={"weight": self.primary_weight.value},
            )
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def secondary_weight(self) -> Percentage:
        return Percentage(round(1.0 - self.primary_weight.value, 4))
