"""The Competitor entity.

A :class:`Competitor` is a brand the engine analyses, tiered by the classifier
into how it relates to the client (primary, aspirational, luxury reference, …). It
is immutable; classification produces a new instance via :meth:`with_tier`.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
the tier value object.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import CompetitorId
from competitive.domain.shared.value_objects import CompetitorTier

__all__ = ["Competitor", "InvalidCompetitorError"]


class InvalidCompetitorError(DesignDirectorError):
    """Raised when a competitor is constructed with invalid data."""

    code = "invalid_competitor"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Competitor:
    """A competitor brand under analysis.

    Attributes:
        id: Competitor identity.
        name: The brand name.
        domain: The primary web domain (e.g. ``"example.com"``).
        tier: How it relates to the client (``UNCLASSIFIED`` until the classifier
            tiers it).
        industry: The industry it operates in.
        market: The target market segment.
        country: The primary country of operation.
        positioning: A short brand-positioning statement.
    """

    id: CompetitorId
    name: str
    domain: str = ""
    tier: CompetitorTier = CompetitorTier.UNCLASSIFIED
    industry: str = ""
    market: str = ""
    country: str = ""
    positioning: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidCompetitorError("Competitor.name must be non-empty.")

    @property
    def is_classified(self) -> bool:
        """Whether the competitor has been assigned a real tier."""
        return self.tier is not CompetitorTier.UNCLASSIFIED

    def with_tier(self, tier: CompetitorTier) -> Competitor:
        """Return a copy classified into ``tier``."""
        return replace(self, tier=tier)

    def with_positioning(self, positioning: str) -> Competitor:
        """Return a copy with a refined positioning statement."""
        return replace(self, positioning=positioning)
