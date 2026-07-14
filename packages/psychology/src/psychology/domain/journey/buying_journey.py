"""The buying journey — the phased psychological path from awareness to advocacy.

A :class:`BuyingJourney` is an ordered set of :class:`BuyingStage` s, one per phase the
model addresses. Each stage states the customer's goal, the dominant motivation, the
anxiety and friction that surface, the trust needed, and the emotion in play — all
cited. This is the psychological map every downstream flow must honour.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    DriverKind,
    EmotionKind,
    JourneyPhase,
)

__all__ = ["BuyingJourney", "BuyingStage", "InvalidJourneyError"]


class InvalidJourneyError(DesignDirectorError):
    """Raised when a journey is constructed with invalid data (e.g. duplicate phase)."""

    code = "invalid_buying_journey"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BuyingStage:
    """One phase of the buying journey.

    Attributes:
        phase: The journey phase this stage covers.
        customer_goal: What the customer is trying to do here.
        dominant_motivation: The motivation driving them at this stage.
        dominant_driver: The driver kind most active here.
        anxieties: The anxieties that surface here.
        frictions: The frictions that surface here.
        trust_needed: The trust the stage must supply.
        emotion: The dominant emotion in play.
        evidence_ids: The evidence supporting the stage.
    """

    phase: JourneyPhase
    customer_goal: str
    dominant_driver: DriverKind
    emotion: EmotionKind
    dominant_motivation: str = ""
    anxieties: tuple[str, ...] = ()
    frictions: tuple[str, ...] = ()
    trust_needed: tuple[str, ...] = ()
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.customer_goal or not self.customer_goal.strip():
            raise InvalidJourneyError("BuyingStage.customer_goal must be non-empty.")
        object.__setattr__(self, "anxieties", tuple(self.anxieties))
        object.__setattr__(self, "frictions", tuple(self.frictions))
        object.__setattr__(self, "trust_needed", tuple(self.trust_needed))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


_PHASE_ORDER = {phase: index for index, phase in enumerate(JourneyPhase)}


@dataclass(frozen=True, slots=True)
class BuyingJourney:
    """An ordered, cited buying journey."""

    stages: tuple[BuyingStage, ...] = ()

    def __post_init__(self) -> None:
        stages = tuple(self.stages)
        seen: set[JourneyPhase] = set()
        for stage in stages:
            if stage.phase in seen:
                raise InvalidJourneyError(
                    "BuyingJourney has duplicate phase.", details={"phase": stage.phase.value}
                )
            seen.add(stage.phase)
        object.__setattr__(
            self, "stages", tuple(sorted(stages, key=lambda s: _PHASE_ORDER[s.phase]))
        )

    @classmethod
    def of(cls, stages: Iterable[BuyingStage]) -> BuyingJourney:
        return cls(stages=tuple(stages))

    def __len__(self) -> int:
        return len(self.stages)

    def __iter__(self):
        return iter(self.stages)

    def stage(self, phase: JourneyPhase) -> BuyingStage | None:
        return next((s for s in self.stages if s.phase is phase), None)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for s in self.stages for eid in s.evidence_ids)
