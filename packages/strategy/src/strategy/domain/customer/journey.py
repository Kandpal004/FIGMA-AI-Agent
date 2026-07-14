"""The customer journey — the phased path from awareness to advocacy.

A :class:`CustomerJourney` is an ordered set of :class:`JourneyStage` s, one per
phase the strategy chooses to address. Each stage states the customer's goal there,
the touchpoints, the pains and objections that surface, the trust it must supply, and
the emotions it should evoke — all cited. This is the strategic map every downstream
flow must honour.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import EmotionKind, JourneyPhase

__all__ = ["CustomerJourney", "InvalidJourneyError", "JourneyStage"]


class InvalidJourneyError(DesignDirectorError):
    """Raised when a journey is constructed with invalid data (e.g. duplicate phase)."""

    code = "invalid_customer_journey"
    http_status = 422


@dataclass(frozen=True, slots=True)
class JourneyStage:
    """One phase of the customer journey.

    Attributes:
        phase: The journey phase this stage covers.
        customer_goal: What the customer is trying to do here.
        touchpoints: The strategic touchpoints in play (not UI screens).
        pains: The pains that surface here.
        objections: The objections that surface here.
        required_trust: The trust the stage must supply.
        emotions: The emotions the stage should evoke.
        evidence_ids: The evidence supporting the stage.
    """

    phase: JourneyPhase
    customer_goal: str
    touchpoints: tuple[str, ...] = ()
    pains: tuple[str, ...] = ()
    objections: tuple[str, ...] = ()
    required_trust: tuple[str, ...] = ()
    emotions: tuple[EmotionKind, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.customer_goal or not self.customer_goal.strip():
            raise InvalidJourneyError("JourneyStage.customer_goal must be non-empty.")
        object.__setattr__(self, "touchpoints", tuple(self.touchpoints))
        object.__setattr__(self, "pains", tuple(self.pains))
        object.__setattr__(self, "objections", tuple(self.objections))
        object.__setattr__(self, "required_trust", tuple(self.required_trust))
        object.__setattr__(self, "emotions", tuple(self.emotions))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


_PHASE_ORDER = {phase: index for index, phase in enumerate(JourneyPhase)}


@dataclass(frozen=True, slots=True)
class CustomerJourney:
    """An ordered, cited customer journey."""

    stages: tuple[JourneyStage, ...] = ()

    def __post_init__(self) -> None:
        stages = tuple(self.stages)
        seen: set[JourneyPhase] = set()
        for stage in stages:
            if stage.phase in seen:
                raise InvalidJourneyError(
                    "CustomerJourney has duplicate phase.",
                    details={"phase": stage.phase.value},
                )
            seen.add(stage.phase)
        ordered = tuple(sorted(stages, key=lambda s: _PHASE_ORDER[s.phase]))
        object.__setattr__(self, "stages", ordered)

    @classmethod
    def of(cls, stages: Iterable[JourneyStage]) -> CustomerJourney:
        return cls(stages=tuple(stages))

    def __len__(self) -> int:
        return len(self.stages)

    def __iter__(self):
        return iter(self.stages)

    def stage(self, phase: JourneyPhase) -> JourneyStage | None:
        return next((s for s in self.stages if s.phase is phase), None)

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return tuple(eid for s in self.stages for eid in s.evidence_ids)
