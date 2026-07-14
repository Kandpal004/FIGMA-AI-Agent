"""The CategoryScore — one of the fifteen scores the Creative Director assigns.

A :class:`CategoryScore` is the engine's 0–100 rating of one scoring category (business,
brand, conversion, accessibility, …), the weight that category carries under the active
profile, and the review dimensions that contributed to it. The weighted roll-up of the
substantive categories produces the ``OVERALL`` score the approval threshold is measured
against.

Pure domain: standard library, the shared-kernel error base, CD ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.shared.ids import CDEvidenceId
from creative_director.domain.shared.value_objects import (
    QualityBand,
    ReviewDimension,
    Score,
    ScoreCategory,
    Weight,
)

__all__ = ["CategoryScore", "InvalidCategoryScoreError"]


class InvalidCategoryScoreError(DesignDirectorError):
    """Raised when a category score is constructed with invalid data."""

    code = "invalid_creative_director_category_score"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CategoryScore:
    """The Creative Director's rating of one scoring category.

    Attributes:
        category: The scoring category.
        score: The 0–100 rating.
        weight: The category's share of the overall score under the active profile.
        dimensions: The review dimensions that contributed to it.
        evidence_ids: The evidence grounding the score.
    """

    category: ScoreCategory
    score: Score
    weight: Weight
    dimensions: tuple[ReviewDimension, ...] = ()
    evidence_ids: tuple[CDEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimensions", tuple(dict.fromkeys(self.dimensions)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def band(self) -> QualityBand:
        return self.score.band

    def all_evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return self.evidence_ids
