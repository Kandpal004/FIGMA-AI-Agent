"""The Scorecard — the Creative Director's fifteen scores, together.

A :class:`Scorecard` bundles the fourteen substantive :class:`CategoryScore` s plus the
derived ``OVERALL`` roll-up. It is the quantitative basis of the approval decision: the
threshold is measured against ``OVERALL`` and the profile's hard gates are measured against
the individual categories.

Pure domain: standard library, the shared-kernel error base, and the category-score model.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.scoring.category_score import CategoryScore
from creative_director.domain.shared.ids import CDEvidenceId
from creative_director.domain.shared.value_objects import Score, ScoreCategory

__all__ = ["InvalidScorecardError", "Scorecard"]


class InvalidScorecardError(DesignDirectorError):
    """Raised when a scorecard is constructed with invalid data (missing/duplicate)."""

    code = "invalid_creative_director_scorecard"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Scorecard:
    """The Creative Director's complete set of category scores."""

    scores: tuple[CategoryScore, ...]

    def __post_init__(self) -> None:
        seen: set[ScoreCategory] = set()
        for cs in self.scores:
            if cs.category in seen:
                raise InvalidScorecardError(
                    "Duplicate category in scorecard.", details={"category": cs.category.value}
                )
            seen.add(cs.category)
        if ScoreCategory.OVERALL not in seen:
            raise InvalidScorecardError("Scorecard must include the OVERALL score.")
        object.__setattr__(self, "scores", tuple(self.scores))

    @classmethod
    def of(cls, scores: Iterable[CategoryScore]) -> Scorecard:
        return cls(scores=tuple(scores))

    def get(self, category: ScoreCategory) -> CategoryScore | None:
        return next((cs for cs in self.scores if cs.category is category), None)

    @property
    def overall(self) -> Score:
        overall = self.get(ScoreCategory.OVERALL)
        assert overall is not None  # guaranteed by the invariant
        return overall.score

    def substantive(self) -> tuple[CategoryScore, ...]:
        """Every category score except the OVERALL roll-up."""
        return tuple(cs for cs in self.scores if cs.category is not ScoreCategory.OVERALL)

    def weakest(self) -> CategoryScore | None:
        substantive = self.substantive()
        return min(substantive, key=lambda cs: cs.score.value) if substantive else None

    def evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return tuple(eid for cs in self.scores for eid in cs.all_evidence_ids())
