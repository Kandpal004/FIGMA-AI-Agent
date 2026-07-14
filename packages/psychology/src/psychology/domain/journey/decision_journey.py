"""The decision journey — the micro-commitments within the buying journey.

A :class:`DecisionJourney` models the sequence of small yes-decisions the customer makes
on the way to purchase, each a :class:`DecisionStage`. Every stage carries the anxiety at
that step and a **Peak-End weight** — the recognition (Kahneman) that a few moments (the
emotional peak and the ending) disproportionately shape how the whole experience is
remembered, so design effort should concentrate there.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import EmotionKind, Intensity

__all__ = ["DecisionJourney", "DecisionStage", "InvalidDecisionJourneyError"]


class InvalidDecisionJourneyError(DesignDirectorError):
    """Raised when a decision journey is constructed with invalid data."""

    code = "invalid_decision_journey"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DecisionStage:
    """One micro-commitment on the way to purchase.

    Attributes:
        order: The 1-based position of this step in the journey.
        commitment: The small yes the customer gives here.
        micro_decision: The decision they weigh at this step.
        anxiety: The anxiety at this step.
        emotion: The emotion at this step.
        peak_end_weight: How much this moment shapes the remembered experience (1–5).
        evidence_ids: The evidence supporting it.
    """

    order: int
    commitment: str
    emotion: EmotionKind
    peak_end_weight: Intensity
    micro_decision: str = ""
    anxiety: str = ""
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.order < 1:
            raise InvalidDecisionJourneyError("DecisionStage.order must be >= 1.")
        if not self.commitment or not self.commitment.strip():
            raise InvalidDecisionJourneyError("DecisionStage.commitment must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def is_peak_moment(self) -> bool:
        """Whether this is a high-weight (peak) moment worth concentrating effort on."""
        return int(self.peak_end_weight) >= 4


@dataclass(frozen=True, slots=True)
class DecisionJourney:
    """An ordered, cited sequence of micro-commitments."""

    stages: tuple[DecisionStage, ...] = ()

    def __post_init__(self) -> None:
        stages = tuple(sorted(self.stages, key=lambda s: s.order))
        orders = [s.order for s in stages]
        if len(set(orders)) != len(orders):
            raise InvalidDecisionJourneyError(
                "DecisionJourney has duplicate step orders.", details={"orders": orders}
            )
        object.__setattr__(self, "stages", stages)

    @classmethod
    def of(cls, stages: Iterable[DecisionStage]) -> DecisionJourney:
        return cls(stages=tuple(stages))

    def __len__(self) -> int:
        return len(self.stages)

    def __iter__(self):
        return iter(self.stages)

    def peak_moments(self) -> tuple[DecisionStage, ...]:
        """The high-weight moments (peaks) plus the ending — where memory forms."""
        peaks = [s for s in self.stages if s.is_peak_moment]
        if self.stages and self.stages[-1] not in peaks:
            peaks.append(self.stages[-1])
        return tuple(peaks)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for s in self.stages for eid in s.evidence_ids)
