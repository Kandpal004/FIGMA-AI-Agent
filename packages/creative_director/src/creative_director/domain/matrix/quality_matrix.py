"""The QualityMatrix — the scorecard as an at-a-glance grid.

A :class:`QualityMatrix` projects the :class:`Scorecard` into a category-by-quality grid: for
each scoring category, its score, band, and weight. It is a read model the facade exposes so
a reviewer (or a console) can see the whole quality picture in one place.

Pure domain: standard library, the shared-kernel error base, and the scoring models.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.value_objects import QualityBand, Score, ScoreCategory, Weight

__all__ = ["QualityCell", "QualityMatrix"]


@dataclass(frozen=True, slots=True)
class QualityCell:
    """One category's quality at a glance."""

    category: ScoreCategory
    score: Score
    band: QualityBand
    weight: Weight


@dataclass(frozen=True, slots=True)
class QualityMatrix:
    """The scorecard projected into a category-by-quality grid."""

    cells: tuple[QualityCell, ...]

    @classmethod
    def from_scorecard(cls, scorecard: Scorecard) -> QualityMatrix:
        return cls(cells=tuple(
            QualityCell(category=cs.category, score=cs.score, band=cs.band, weight=cs.weight)
            for cs in scorecard.scores
        ))

    def get(self, category: ScoreCategory) -> QualityCell | None:
        return next((c for c in self.cells if c.category is category), None)
