"""Stage — Matrix construction.

Assembles the nine psychology matrices from the validated draft: some are lifted from
the psychological profile (trust, motivation, emotion, risk, confidence), others come
directly from the judgement-bearing draft inputs (objection, behavior, value, retention).
Every cell carries the evidence of the finding it is built from, so the matrices are
grounded in the same evidence as the model.
"""

from __future__ import annotations

from psychology.application.contracts import PsychologyDraft
from psychology.domain.matrices.cells import (
    ConfidenceCell,
    EmotionCell,
    MotivationCell,
    RiskCell,
    TrustCell,
)
from psychology.domain.matrices.matrices import (
    BehaviorMatrix,
    ConfidenceMatrix,
    EmotionMatrix,
    MotivationMatrix,
    ObjectionMatrix,
    PsychologyMatrices,
    RetentionMatrix,
    RiskMatrix,
    TrustMatrix,
    ValueMatrix,
)
from psychology.domain.shared.ids import MatrixCellId
from psychology.domain.shared.value_objects import (
    DriverKind,
    EmotionKind,
    Intensity,
    MaslowNeed,
)

__all__ = ["MatrixBuilder"]

_NEED_DRIVER: dict[MaslowNeed, DriverKind] = {
    MaslowNeed.PHYSIOLOGICAL: DriverKind.LOGICAL,
    MaslowNeed.SAFETY: DriverKind.LOGICAL,
    MaslowNeed.BELONGING: DriverKind.SOCIAL,
    MaslowNeed.ESTEEM: DriverKind.SOCIAL,
    MaslowNeed.SELF_ACTUALIZATION: DriverKind.EMOTIONAL,
}

_NEGATIVE_EMOTIONS = {EmotionKind.ANXIETY, EmotionKind.FEAR, EmotionKind.REGRET}


class MatrixBuilder:
    """Builds the nine psychology matrices from a validated draft."""

    def build(self, draft: PsychologyDraft) -> PsychologyMatrices:
        profile = draft.profile
        return PsychologyMatrices(
            objection=ObjectionMatrix.of(draft.objections),
            behavior=BehaviorMatrix.of(draft.behaviors),
            value=ValueMatrix.of(draft.value_cells),
            retention=RetentionMatrix.of(draft.retention_cells),
            trust=TrustMatrix.of(
                TrustCell(
                    id=MatrixCellId.new(), requirement=t.description, kind=t.kind,
                    signal_needed=f"Provide credible {t.kind.value.replace('_', ' ')}.",
                    phase=t.phase, salience=Intensity(int(t.priority)), evidence_ids=t.evidence_ids,
                )
                for t in profile.trust_requirements
            ),
            motivation=MotivationMatrix.of(
                MotivationCell(
                    id=MatrixCellId.new(), motivation=m.description, maslow_need=m.maslow_need,
                    driver_kind=_NEED_DRIVER[m.maslow_need], intensity=m.intensity,
                    evidence_ids=m.evidence_ids,
                )
                for m in profile.motivations
            ),
            emotion=EmotionMatrix.of(
                EmotionCell(
                    id=MatrixCellId.new(), emotion=s.emotion, phase=s.phase,
                    trigger=s.dominant_motivation or s.customer_goal,
                    intended_shift=(
                        EmotionKind.REASSURANCE if s.emotion in _NEGATIVE_EMOTIONS
                        else EmotionKind.CONFIDENCE
                    ),
                    evidence_ids=s.evidence_ids,
                )
                for s in draft.buying_journey
            ),
            risk=RiskMatrix.of(
                RiskCell(
                    id=MatrixCellId.new(), risk=r.description, kind=r.kind,
                    likelihood=r.likelihood, impact=r.impact, mitigation=r.mitigation,
                    evidence_ids=r.evidence_ids,
                )
                for r in profile.risks
            ),
            confidence=ConfidenceMatrix.of(self._confidence_cells(profile)),
        )

    @staticmethod
    def _confidence_cells(profile):
        conf = profile.confidence
        cells = []
        for blocker in conf.blockers:
            cells.append(
                ConfidenceCell(
                    id=MatrixCellId.new(), factor=blocker, current_level=Intensity(2),
                    lever=f"Address: {blocker}", evidence_ids=conf.evidence_ids,
                )
            )
        for booster in conf.boosters:
            cells.append(
                ConfidenceCell(
                    id=MatrixCellId.new(), factor=booster, current_level=Intensity(4),
                    lever=f"Amplify: {booster}", evidence_ids=conf.evidence_ids,
                )
            )
        if not cells:
            cells.append(
                ConfidenceCell(
                    id=MatrixCellId.new(), factor="overall purchase confidence",
                    current_level=conf.level, lever="Reinforce trust and reduce risk.",
                    evidence_ids=conf.evidence_ids,
                )
            )
        return cells
