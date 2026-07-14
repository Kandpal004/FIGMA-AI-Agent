"""The Recommendation matrix — the engine's actionable, evidence-backed output.

A :class:`Recommendation` is an action (adopt / avoid / monitor) on a dimension,
justified by a rationale and — mandatorily — Knowledge citations. An ungrounded
recommendation cannot be constructed: this is where "no opinion-based
recommendations" is enforced. :class:`RecommendationMatrix` groups them by action
and priority.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import EvidenceId, PatternId, RecommendationId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
    RecommendationAction,
    Severity,
)

__all__ = ["InvalidRecommendationError", "Recommendation", "RecommendationMatrix"]


class InvalidRecommendationError(DesignDirectorError):
    """Raised when a recommendation is constructed without grounding."""

    code = "invalid_recommendation"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Recommendation:
    """One evidence-backed recommendation.

    Attributes:
        id: Recommendation identity.
        action: Adopt / avoid / monitor.
        dimension: The dimension it concerns.
        title: A short title.
        rationale: Why it is recommended (grounded in the evidence).
        priority: How important it is.
        confidence: Confidence in the recommendation.
        evidence_ids: Knowledge citations backing it (must be non-empty).
        pattern_id: The pattern it derives from, if any.
    """

    id: RecommendationId
    action: RecommendationAction
    dimension: CompetitorDimension
    title: str
    rationale: str
    priority: Severity
    confidence: Confidence
    evidence_ids: tuple[EvidenceId, ...] = ()
    pattern_id: PatternId | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidRecommendationError("Recommendation.title must be non-empty.")
        if not self.rationale or not self.rationale.strip():
            raise InvalidRecommendationError("Recommendation.rationale must be non-empty.")
        normalized = tuple(self.evidence_ids)
        if not normalized:
            raise InvalidRecommendationError(
                "A recommendation must cite Knowledge evidence (no opinions).",
                details={"title": self.title},
            )
        object.__setattr__(self, "evidence_ids", normalized)


@dataclass(frozen=True, slots=True)
class RecommendationMatrix:
    """The engine's recommendations, grouped by action and priority."""

    recommendations: tuple[Recommendation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "recommendations", tuple(self.recommendations))

    def __len__(self) -> int:
        return len(self.recommendations)

    def _of(self, action: RecommendationAction) -> tuple[Recommendation, ...]:
        return tuple(r for r in self.recommendations if r.action is action)

    def to_adopt(self) -> tuple[Recommendation, ...]:
        return self._of(RecommendationAction.ADOPT)

    def to_avoid(self) -> tuple[Recommendation, ...]:
        return self._of(RecommendationAction.AVOID)

    def to_monitor(self) -> tuple[Recommendation, ...]:
        return self._of(RecommendationAction.MONITOR)

    def by_priority(self) -> tuple[Recommendation, ...]:
        """Recommendations ranked by priority (highest first)."""
        return tuple(sorted(self.recommendations, key=lambda r: int(r.priority), reverse=True))
