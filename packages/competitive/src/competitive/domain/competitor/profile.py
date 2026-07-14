"""The Competitor profile — a competitor synthesised across every dimension.

A :class:`DimensionAssessment` is the engine's synthesis of a competitor's
observations for one dimension into a benchmark :class:`Score` plus a summary and a
confidence. A :class:`CompetitorProfile` gathers one assessment per profiled
dimension, together with the competitor's strengths, weaknesses, opportunities, and
threats.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import CompetitorId, ProfileId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
    Score,
)

__all__ = ["CompetitorProfile", "DimensionAssessment", "InvalidProfileError"]


class InvalidProfileError(DesignDirectorError):
    """Raised when a profile or assessment is constructed with invalid data."""

    code = "invalid_profile"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DimensionAssessment:
    """A competitor's synthesised standing on one dimension.

    Attributes:
        dimension: The dimension assessed.
        score: The 0–100 benchmark score.
        summary: A short synthesis of the supporting observations.
        confidence: Confidence in the assessment.
        observation_count: How many observations informed it.
    """

    dimension: CompetitorDimension
    score: Score
    summary: str
    confidence: Confidence
    observation_count: int = 0

    def __post_init__(self) -> None:
        if self.observation_count < 0:
            raise InvalidProfileError("DimensionAssessment.observation_count must be >= 0.")


@dataclass(frozen=True, slots=True)
class CompetitorProfile:
    """A competitor's full profile across the analysed dimensions.

    Attributes:
        id: Profile identity.
        competitor_id: The competitor profiled.
        assessments: One assessment per profiled dimension (unique by dimension).
        strengths: What the competitor does notably well.
        weaknesses: Where the competitor is notably weak.
        opportunities: Openings the competitor could exploit.
        threats: Threats the competitor faces.
    """

    id: ProfileId
    competitor_id: CompetitorId
    assessments: tuple[DimensionAssessment, ...] = ()
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    opportunities: tuple[str, ...] = ()
    threats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        seen: set[CompetitorDimension] = set()
        for assessment in self.assessments:
            if assessment.dimension in seen:
                raise InvalidProfileError(
                    "Duplicate dimension in profile.",
                    details={"dimension": assessment.dimension.value},
                )
            seen.add(assessment.dimension)
        object.__setattr__(self, "assessments", tuple(self.assessments))
        object.__setattr__(self, "strengths", tuple(self.strengths))
        object.__setattr__(self, "weaknesses", tuple(self.weaknesses))
        object.__setattr__(self, "opportunities", tuple(self.opportunities))
        object.__setattr__(self, "threats", tuple(self.threats))

    def assessment_for(
        self, dimension: CompetitorDimension
    ) -> DimensionAssessment | None:
        """The assessment for a dimension, or ``None`` if not assessed."""
        for assessment in self.assessments:
            if assessment.dimension is dimension:
                return assessment
        return None

    def score_for(self, dimension: CompetitorDimension) -> Score | None:
        """The benchmark score for a dimension, or ``None`` if not assessed."""
        assessment = self.assessment_for(dimension)
        return assessment.score if assessment else None
