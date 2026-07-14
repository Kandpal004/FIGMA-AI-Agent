"""PatternAnalyzer — detects recurring patterns across competitor profiles.

A dimension on which many competitors score strongly is a *recurring pattern*. If
it is dominant (≥ half the category) **and** grounded in Knowledge evidence, it is
recommended for adoption; otherwise it is flagged to monitor. It never recommends
adoption without evidence — that keeps the output opinion-free. Deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.profile import CompetitorProfile
from competitive.domain.evidence.evidence import EvidenceRef
from competitive.domain.pattern.pattern import PatternInstance, RecurringPattern
from competitive.domain.shared.ids import PatternId
from competitive.domain.shared.value_objects import (
    CompetitorDimension as Dim,
    Confidence,
    PatternKind,
    RecommendationAction,
)

__all__ = ["PatternAnalyzer"]

_STRONG = 70.0

_DIMENSION_KIND: dict[Dim, PatternKind] = {
    Dim.CONVERSION_PATTERNS: PatternKind.CRO,
    Dim.CHECKOUT_STRATEGY: PatternKind.CRO,
    Dim.TRUST_STRATEGY: PatternKind.TRUST,
    Dim.VISUAL_LANGUAGE: PatternKind.VISUAL,
    Dim.TYPOGRAPHY: PatternKind.VISUAL,
    Dim.SPACING: PatternKind.VISUAL,
    Dim.NAVIGATION: PatternKind.NAVIGATION,
    Dim.INFORMATION_ARCHITECTURE: PatternKind.NAVIGATION,
    Dim.HOMEPAGE_STRUCTURE: PatternKind.CONTENT,
    Dim.COLLECTION_STRATEGY: PatternKind.MERCHANDISING,
    Dim.PRODUCT_PAGE_STRATEGY: PatternKind.MERCHANDISING,
    Dim.MOBILE_STRATEGY: PatternKind.UX,
    Dim.ACCESSIBILITY: PatternKind.ACCESSIBILITY,
    Dim.PERFORMANCE: PatternKind.PERFORMANCE,
    Dim.SEO: PatternKind.SEO,
    Dim.BRAND_POSITIONING: PatternKind.UX,
}


class PatternAnalyzer:
    """Detects recurring, evidence-grounded patterns across profiles."""

    def detect(
        self,
        profiles: tuple[CompetitorProfile, ...],
        competitors: tuple[Competitor, ...],
        evidence_by_dimension: Mapping[Dim, tuple[EvidenceRef, ...]],
    ) -> tuple[RecurringPattern, ...]:
        total = len(competitors)
        if total == 0:
            return ()

        dimensions: list[Dim] = []
        for profile in profiles:
            for assessment in profile.assessments:
                if assessment.dimension not in dimensions:
                    dimensions.append(assessment.dimension)

        patterns: list[RecurringPattern] = []
        for dimension in dimensions:
            exhibitors = [
                p.competitor_id
                for p in profiles
                if (s := p.score_for(dimension)) is not None and s.value >= _STRONG
            ]
            if not exhibitors:
                continue
            ratio = len(exhibitors) / total
            if ratio < 0.25:  # not recurring enough
                continue

            evidence = evidence_by_dimension.get(dimension, ())
            if ratio >= 0.5 and evidence:
                action = RecommendationAction.ADOPT
                evidence_ids = [e.id for e in evidence]
            else:
                action = RecommendationAction.MONITOR
                evidence_ids = []

            label = dimension.value.replace("_", " ")
            patterns.append(
                RecurringPattern.from_instances(
                    id=PatternId.new(),
                    kind=_DIMENSION_KIND.get(dimension, PatternKind.UX),
                    dimension=dimension,
                    name=f"Strong {label}",
                    description=f"{len(exhibitors)} of {total} competitors show strong {label}.",
                    instances=[PatternInstance(cid, dimension) for cid in exhibitors],
                    total_competitors=total,
                    action=action,
                    confidence=Confidence.clamp(0.5 + 0.5 * ratio),
                    evidence_ids=evidence_ids,
                )
            )
        return tuple(patterns)
