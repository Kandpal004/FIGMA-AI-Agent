"""Stage — Quality scoring.

Computes the report's calibrated quality picture deterministically:

* **coverage** — how many of the required outputs the model produced.
* **grounding** — the fraction of findings whose citations resolve (``1.0`` by
  construction, surfaced here so the metric is auditable).
* **framework_validation** — the fraction of the required behavioral frameworks
  (Maslow / Fogg / Hook / JTBD / behavioral economics) actually applied.
* **confidence** — the aggregate confidence across the model.
"""

from __future__ import annotations

from psychology.application.contracts import PsychologyDraft
from psychology.domain.frameworks.lens import FrameworkLens
from psychology.domain.matrices.matrices import PsychologyMatrices
from psychology.domain.quality.quality import PsychologyQualityMetrics
from psychology.domain.shared.value_objects import (
    Confidence,
    Percentage,
    PsychFramework,
)

__all__ = ["QualityScorer"]

_REQUIRED_FRAMEWORKS = 5  # Maslow, Fogg, Hook, JTBD, behavioral economics


class QualityScorer:
    """Scores the model's coverage, grounding, framework validation, and confidence."""

    def score(
        self,
        draft: PsychologyDraft,
        matrices: PsychologyMatrices,
        frameworks: FrameworkLens,
    ) -> PsychologyQualityMetrics:
        coverage = Percentage.ratio(*self._coverage(draft, matrices, frameworks))
        grounding = Percentage.ratio(*self._grounding(draft, matrices))
        applied = set(frameworks.applied_frameworks())
        if len(draft.jobs):
            applied.add(PsychFramework.JTBD)
        framework_validation = Percentage.ratio(len(applied), _REQUIRED_FRAMEWORKS)
        return PsychologyQualityMetrics(
            coverage=coverage,
            grounding=grounding,
            framework_validation=framework_validation,
            confidence=self._confidence(draft),
        )

    @staticmethod
    def _coverage(
        draft: PsychologyDraft, matrices: PsychologyMatrices, frameworks: FrameworkLens
    ) -> tuple[int, int]:
        checklist = (
            bool(draft.profile.target_customer),
            bool(len(draft.personas)),
            bool(len(draft.buying_personas)),
            bool(len(draft.jobs)),
            bool(len(draft.buying_journey)),
            bool(len(draft.decision_journey)),
            bool(len(matrices.objection)),
            bool(len(matrices.trust)),
            bool(len(matrices.motivation)),
            bool(len(matrices.emotion)),
            bool(len(matrices.behavior)),
            bool(len(matrices.risk)),
            bool(len(matrices.value)),
            bool(len(matrices.confidence)),
            bool(len(matrices.retention)),
            bool(frameworks.maslow.dominant_need),
            bool(frameworks.fogg.conclusion),
            bool(len(frameworks.principles)),
        )
        return sum(1 for present in checklist if present), len(checklist)

    @staticmethod
    def _grounding(
        draft: PsychologyDraft, matrices: PsychologyMatrices
    ) -> tuple[int, int]:
        findings = [
            *matrices.objection, *matrices.trust, *matrices.motivation, *matrices.emotion,
            *matrices.behavior, *matrices.risk, *matrices.value, *matrices.confidence,
            *matrices.retention,
            *draft.profile.motivations, *draft.profile.anxieties, *draft.profile.risks,
            *draft.profile.trust_requirements, *draft.profile.decision_triggers,
        ]
        if not findings:
            return 0, 1
        grounded = sum(1 for f in findings if f.evidence_ids)
        return grounded, len(findings)

    @staticmethod
    def _confidence(draft: PsychologyDraft) -> Confidence:
        values = [p.confidence.value for p in draft.personas]
        values.append(int(draft.profile.confidence.level) / 5.0)
        return Confidence.clamp(sum(values) / len(values)) if values else Confidence.of(0.5)
