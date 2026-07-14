"""Stage — Quality scoring.

Computes the report's calibrated quality picture deterministically:

* **coverage** — how many of the required outputs the strategy produced.
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by
  construction, surfaced here so the metric is auditable).
* **heuristic_validation** — the fraction of the eleven UX laws actually applied.
* **confidence** — the aggregate confidence across the strategy.
"""

from __future__ import annotations

from ux.application.contracts import UXDraft
from ux.domain.analysis.dropoff import DropoffAnalysis
from ux.domain.analysis.friction import FrictionAnalysis
from ux.domain.laws.lens import UXLawLens
from ux.domain.quality.quality import UXQualityMetrics
from ux.domain.shared.value_objects import Confidence, Percentage, UXLaw

__all__ = ["QualityScorer"]

_REQUIRED_LAWS = len(UXLaw)  # eleven


class QualityScorer:
    """Scores the strategy's coverage, grounding, heuristic validation, and confidence."""

    def score(
        self,
        draft: UXDraft,
        laws: UXLawLens,
        friction: FrictionAnalysis,
        dropoff: DropoffAnalysis,
    ) -> UXQualityMetrics:
        coverage = Percentage.ratio(*self._coverage(draft, laws, friction, dropoff))
        grounding = Percentage.ratio(*self._grounding(draft, laws))
        heuristic = Percentage.ratio(len(laws.laws()), _REQUIRED_LAWS)
        return UXQualityMetrics(
            coverage=coverage,
            grounding=grounding,
            heuristic_validation=heuristic,
            confidence=self._confidence(draft),
        )

    @staticmethod
    def _coverage(
        draft: UXDraft,
        laws: UXLawLens,
        friction: FrictionAnalysis,
        dropoff: DropoffAnalysis,
    ) -> tuple[int, int]:
        journeys = draft.journeys
        checklist = (
            draft.goals.primary_user_goal is not None,
            bool(draft.goals.business_goals),
            bool(draft.mental_model.summary),
            bool(len(draft.pages)),
            bool(len(journeys.user)),
            bool(len(journeys.task)),
            bool(len(journeys.decision)),
            bool(len(journeys.trust)),
            bool(len(journeys.conversion)),
            bool(len(journeys.mobile)),
            bool(len(journeys.accessibility)),
            bool(len(draft.flows)),
            bool(draft.strategies.navigation.pattern),
            bool(draft.strategies.content.hierarchy_intent),
            bool(draft.strategies.interaction.patterns),
            bool(draft.strategies.error_recovery.recovery),
            bool(draft.strategies.disclosure.reveal_first),
            bool(draft.strategies.trust.trust_moments),
            bool(len(friction)),
            bool(len(dropoff)),
            bool(len(laws)),
        )
        return sum(1 for present in checklist if present), len(checklist)

    @staticmethod
    def _grounding(draft: UXDraft, laws: UXLawLens) -> tuple[int, int]:
        # Grounding over the citable leaf decisions: page strategies, law applications,
        # and journey stages.
        citable: list[tuple[object, tuple]] = [
            (p, p.all_evidence_ids()) for p in draft.pages
        ]
        citable.extend((a, a.evidence_ids) for a in laws)
        for journey in draft.journeys.all():
            for stage in journey:
                citable.append((stage, stage.evidence_ids))
        if not citable:
            return 0, 1
        grounded = sum(1 for _, ev in citable if ev)
        return grounded, len(citable)

    @staticmethod
    def _confidence(draft: UXDraft) -> Confidence:
        # A modest, deterministic confidence anchored on how richly the pages are specified.
        pages = tuple(draft.pages)
        if not pages:
            return Confidence.of(0.0)
        detailed = sum(1 for p in pages if p.ctas and p.success_metrics)
        return Confidence.clamp(0.5 + 0.5 * (detailed / len(pages)))
