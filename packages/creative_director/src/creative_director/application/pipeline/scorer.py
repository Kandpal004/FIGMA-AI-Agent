"""Stage — Scoring.

Rolls the sixteen dimension reviews up into the fifteen category scores. Each
:class:`ReviewDimension` contributes to one or more :class:`ScoreCategory` via a fixed map;
a category's score is the mean of its contributing dimensions' quality scores. The ``OVERALL``
roll-up is the profile-weighted mean of the substantive categories — so the *same* critic
outputs yield different overalls under different profiles (Luxury weights brand/typography/
trust; Marketplace weights conversion/performance), without any rescoring.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.domain.policy.profile import ReviewProfile
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.category_score import CategoryScore
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.ids import CDEvidenceId
from creative_director.domain.shared.value_objects import (
    ReviewDimension,
    Score,
    ScoreCategory,
    Weight,
)

__all__ = ["DIMENSION_TO_CATEGORIES", "Scorer"]

# Which scoring categories each review dimension feeds.
DIMENSION_TO_CATEGORIES: dict[ReviewDimension, tuple[ScoreCategory, ...]] = {
    ReviewDimension.BUSINESS_ALIGNMENT: (ScoreCategory.BUSINESS,),
    ReviewDimension.BRAND_ALIGNMENT: (ScoreCategory.BRAND, ScoreCategory.CONSISTENCY),
    ReviewDimension.PSYCHOLOGY_ALIGNMENT: (ScoreCategory.TRUST, ScoreCategory.CONVERSION),
    ReviewDimension.UX_QUALITY: (ScoreCategory.UX,),
    ReviewDimension.INFORMATION_HIERARCHY: (ScoreCategory.VISUAL_HIERARCHY, ScoreCategory.CONSISTENCY),
    ReviewDimension.CONVERSION_STRATEGY: (ScoreCategory.CONVERSION,),
    ReviewDimension.TRUST_SIGNALS: (ScoreCategory.TRUST,),
    ReviewDimension.TYPOGRAPHY_DIRECTION: (ScoreCategory.TYPOGRAPHY, ScoreCategory.CONSISTENCY),
    ReviewDimension.SPACING_LOGIC: (ScoreCategory.SPACING, ScoreCategory.CONSISTENCY),
    ReviewDimension.ACCESSIBILITY: (ScoreCategory.ACCESSIBILITY,),
    ReviewDimension.PERFORMANCE_IMPACT: (ScoreCategory.PERFORMANCE,),
    ReviewDimension.MOBILE_EXPERIENCE: (ScoreCategory.UX, ScoreCategory.PERFORMANCE),
    ReviewDimension.DEVELOPER_FEASIBILITY: (ScoreCategory.DEVELOPER_EXPERIENCE, ScoreCategory.MAINTAINABILITY),
    ReviewDimension.SHOPIFY_COMPATIBILITY: (ScoreCategory.DEVELOPER_EXPERIENCE,),
    ReviewDimension.MAGENTO_COMPATIBILITY: (ScoreCategory.DEVELOPER_EXPERIENCE,),
    ReviewDimension.FUTURE_SCALABILITY: (ScoreCategory.SCALABILITY, ScoreCategory.MAINTAINABILITY),
}


class Scorer:
    """Rolls dimension reviews up into a profile-weighted scorecard."""

    def score(
        self, dimension_reviews: Sequence[DimensionReview], profile: ReviewProfile
    ) -> Scorecard:
        # Collect contributing (score, evidence) per category.
        contributions: dict[ScoreCategory, list[DimensionReview]] = {}
        for dr in dimension_reviews:
            for category in DIMENSION_TO_CATEGORIES.get(dr.dimension, ()):
                contributions.setdefault(category, []).append(dr)

        category_scores: list[CategoryScore] = []
        weighted_sum = 0.0
        weight_total = 0.0
        overall_evidence: list[CDEvidenceId] = []

        for category, reviews in contributions.items():
            mean = sum(r.quality_score.value for r in reviews) / len(reviews)
            evidence = tuple(dict.fromkeys(
                eid for r in reviews for eid in r.evidence_ids
            ))
            weight = profile.weight_of(category)
            category_scores.append(
                CategoryScore(
                    category=category, score=Score.clamp(mean), weight=weight,
                    dimensions=tuple(r.dimension for r in reviews), evidence_ids=evidence,
                )
            )
            weighted_sum += weight.value * mean
            weight_total += weight.value
            overall_evidence.extend(evidence)

        overall_value = weighted_sum / weight_total if weight_total > 0 else 0.0
        category_scores.append(
            CategoryScore(
                category=ScoreCategory.OVERALL, score=Score.clamp(overall_value),
                weight=Weight(1.0), dimensions=(),
                evidence_ids=tuple(dict.fromkeys(overall_evidence)),
            )
        )
        return Scorecard.of(category_scores)
