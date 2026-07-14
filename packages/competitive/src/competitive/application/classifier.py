"""Classifier — assigns each competitor a tier, deterministically.

Given a competitor's profile, it derives a :class:`CompetitorTier` from a small,
ordered rule set (conversion strength → conversion leader; strong brand + visual →
aspirational/luxury; broad excellence → innovation leader; otherwise primary or
secondary by overall strength). A competitor that already carries a tier (supplied
in the brief) is left as-is. Deterministic; no I/O.
"""

from __future__ import annotations

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.profile import CompetitorProfile
from competitive.domain.shared.ids import CompetitorId
from competitive.domain.shared.value_objects import CompetitorDimension as Dim
from competitive.domain.shared.value_objects import CompetitorTier

__all__ = ["Classifier"]


class Classifier:
    """Tiers competitors from their profiles."""

    def classify(
        self,
        competitors: tuple[Competitor, ...],
        profiles: tuple[CompetitorProfile, ...],
        *,
        market: str = "",
    ) -> tuple[Competitor, ...]:
        by_competitor: dict[CompetitorId, CompetitorProfile] = {
            p.competitor_id: p for p in profiles
        }
        return tuple(
            competitor
            if competitor.is_classified
            else competitor.with_tier(
                self._tier_for(competitor, by_competitor.get(competitor.id), market)
            )
            for competitor in competitors
        )

    @staticmethod
    def _tier_for(
        competitor: Competitor, profile: CompetitorProfile | None, market: str
    ) -> CompetitorTier:
        if profile is None or not profile.assessments:
            return CompetitorTier.SECONDARY

        def score(dim: Dim) -> float:
            s = profile.score_for(dim)
            return s.value if s else 0.0

        avg = sum(a.score.value for a in profile.assessments) / len(profile.assessments)
        strong_count = sum(1 for a in profile.assessments if a.score.value >= 75.0)
        is_luxury = "luxury" in f"{market} {competitor.market} {competitor.positioning}".lower()

        if score(Dim.CONVERSION_PATTERNS) >= 75.0:
            return CompetitorTier.CONVERSION_LEADER
        if score(Dim.BRAND_POSITIONING) >= 80.0 and score(Dim.VISUAL_LANGUAGE) >= 80.0:
            return CompetitorTier.LUXURY_REFERENCE if is_luxury else CompetitorTier.ASPIRATIONAL
        if strong_count >= 6:
            return CompetitorTier.INNOVATION_LEADER
        if avg >= 60.0:
            return CompetitorTier.PRIMARY
        return CompetitorTier.SECONDARY
