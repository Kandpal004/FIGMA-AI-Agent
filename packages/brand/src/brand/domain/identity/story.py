"""Brand story — the narrative the brand tells.

A :class:`BrandStory` follows a classic arc — the customer's world, the tension they
live with, and the resolution the brand makes possible — with the brand cast as the
guide, not the hero. Cited and singular per report.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["BrandStory", "InvalidStoryError"]


class InvalidStoryError(DesignDirectorError):
    """Raised when a brand story is constructed with invalid data."""

    code = "invalid_brand_story"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandStory:
    """The cited brand narrative arc.

    Attributes:
        headline: The one-line story hook.
        situation: The customer's world today.
        tension: The tension or problem they live with.
        resolution: The change the brand makes possible.
        brand_role: How the brand shows up in the story (the guide).
        evidence_ids: The evidence supporting it.
    """

    headline: str
    situation: str
    tension: str
    resolution: str
    brand_role: str = ""
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("headline", "situation", "tension", "resolution"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise InvalidStoryError(f"BrandStory.{name} must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
