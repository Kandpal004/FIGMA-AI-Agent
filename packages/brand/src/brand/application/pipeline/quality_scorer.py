"""Stage — Quality scoring.

Computes the report's calibrated quality picture deterministically:

* **coverage** — how many of the required brand outputs the draft produced.
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by the
  decision-graph builder's construction, surfaced here so the metric is auditable).
* **coherence** — how well the brand's parts align: does the visual direction derive
  from and express the archetype, is the voice defined, are the governance rules present?
* **confidence** — the mean confidence across the graph's decisions.
"""

from __future__ import annotations

from brand.application.contracts import BrandDraft
from brand.domain.decision.decision_graph import BrandDecisionGraph
from brand.domain.governance.governance_model import BrandGovernance
from brand.domain.quality.quality import BrandQualityMetrics
from brand.domain.shared.value_objects import (
    Confidence,
    DecisionRelation,
    Percentage,
)

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the brand's coverage, grounding, coherence, and confidence."""

    def score(
        self,
        draft: BrandDraft,
        decision_graph: BrandDecisionGraph,
        governance: BrandGovernance,
    ) -> BrandQualityMetrics:
        coverage = Percentage.ratio(*self._coverage(draft, governance))
        decisions = tuple(decision_graph)
        grounded = sum(1 for d in decisions if d.evidence_ids)
        grounding = (
            Percentage.ratio(grounded, len(decisions)) if decisions else Percentage.of(0.0)
        )
        if decisions:
            confidence = Confidence.clamp(
                sum(d.confidence.value for d in decisions) / len(decisions)
            )
        else:
            confidence = Confidence.of(0.0)
        coherence = Percentage.ratio(*self._coherence(draft, decision_graph, governance))
        return BrandQualityMetrics(
            coverage=coverage,
            grounding=grounding,
            coherence=coherence,
            confidence=confidence,
        )

    @staticmethod
    def _coverage(draft: BrandDraft, governance: BrandGovernance) -> tuple[int, int]:
        v = draft.visual
        checklist = (
            bool(draft.identity.positioning.statement),
            bool(draft.identity.mission.statement),
            bool(draft.identity.vision.statement),
            bool(len(draft.identity.values)),
            bool(draft.identity.promise.statement),
            bool(draft.identity.story.headline),
            bool(draft.character.archetype.primary),
            bool(draft.character.personality.traits or draft.character.personality.attributes),
            bool(draft.character.voice.dimensions),
            bool(draft.emotional.positioning.emotional_benefit),
            bool(draft.emotional.trust_signals),
            bool(draft.emotional.differentiators),
            bool(v.logo.intent),
            bool(v.typography.display_voice),
            bool(v.color.temperament),
            bool(v.spacing.density),
            bool(v.photography.treatment),
            bool(v.iconography.style),
            bool(v.motion.character),
            bool(v.ui.feel or v.ui.corner_language),
            bool(v.component.interaction_feel or v.component.emphasis),
            bool(draft.verbal.language_rules.person or draft.verbal.language_rules.forbidden_words),
            bool(draft.verbal.copy_guidelines.cta_style or draft.verbal.copy_guidelines.headline_principles),
            bool(len(governance.consistency)),
            bool(len(governance.validation)),
        )
        return sum(1 for present in checklist if present), len(checklist)

    @staticmethod
    def _coherence(
        draft: BrandDraft,
        decision_graph: BrandDecisionGraph,
        governance: BrandGovernance,
    ) -> tuple[int, int]:
        expresses = sum(
            1 for e in decision_graph.edges if e.relation is DecisionRelation.EXPRESSES
        )
        derives = sum(
            1 for e in decision_graph.edges if e.relation is DecisionRelation.DERIVES_FROM
        )
        checks = (
            # Identity is anchored by a committed positioning.
            bool(draft.identity.positioning.statement),
            # The archetype gives the brand a coherent character.
            draft.character.archetype.primary is not None,
            # Creative direction derives from the identity/archetype spine.
            derives > 0,
            # Creative direction expresses the identity/personality.
            expresses > 0,
            # The voice is concretely defined.
            bool(draft.character.voice.dimensions),
            # The brand is enforceable, not just descriptive.
            bool(len(governance.validation)),
        )
        return sum(1 for ok in checks if ok), len(checks)
