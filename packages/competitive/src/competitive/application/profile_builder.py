"""ProfileBuilder — synthesises a competitor's observations into a profile.

For each dimension a competitor was observed on, it folds the observations into a
single :class:`DimensionAssessment`: a 0–100 score (the mean of observed strengths,
or the mean observation confidence scaled to 100 when no strength is given), a
summary of the findings, and a confidence. Strengths/weaknesses are derived
deterministically from the scores. Pure application logic — no I/O, no randomness.
"""

from __future__ import annotations

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.observation import ObservationSet
from competitive.domain.competitor.profile import CompetitorProfile, DimensionAssessment
from competitive.domain.shared.ids import ProfileId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
    Score,
)

__all__ = ["ProfileBuilder"]

_STRONG = 75.0
_WEAK = 40.0


class ProfileBuilder:
    """Builds a :class:`CompetitorProfile` from a competitor's observations."""

    def build(
        self, competitor: Competitor, observations: ObservationSet
    ) -> CompetitorProfile:
        own = observations.for_competitor(competitor.id)
        dimensions: list[CompetitorDimension] = []
        for observation in own:
            if observation.dimension not in dimensions:
                dimensions.append(observation.dimension)

        assessments: list[DimensionAssessment] = []
        for dimension in dimensions:
            obs = observations.select(competitor.id, dimension)
            strengths = [o.strength.value for o in obs if o.strength is not None]
            if strengths:
                score_value = sum(strengths) / len(strengths)
            else:
                score_value = (sum(o.confidence.value for o in obs) / len(obs)) * 100.0
            confidence_value = sum(o.confidence.value for o in obs) / len(obs)
            summary = "; ".join(o.finding for o in obs)
            assessments.append(
                DimensionAssessment(
                    dimension=dimension,
                    score=Score.clamp(score_value),
                    summary=summary,
                    confidence=Confidence.clamp(confidence_value),
                    observation_count=len(obs),
                )
            )

        strengths_out = tuple(
            f"Strong {a.dimension.value.replace('_', ' ')}"
            for a in assessments
            if a.score.value >= _STRONG
        )
        weaknesses_out = tuple(
            f"Weak {a.dimension.value.replace('_', ' ')}"
            for a in assessments
            if a.score.value < _WEAK
        )
        return CompetitorProfile(
            id=ProfileId.new(),
            competitor_id=competitor.id,
            assessments=tuple(assessments),
            strengths=strengths_out,
            weaknesses=weaknesses_out,
        )
