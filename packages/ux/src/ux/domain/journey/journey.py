"""The UX Journey primitive — the shared structure behind the seven journeys.

A :class:`UXJourney` is a typed (:class:`JourneyKind`), ordered set of
:class:`JourneyStage` s. One primitive backs all seven required journeys — User, Task,
Decision, Trust, Conversion, Mobile, Accessibility — each an instance distinguished by
its kind and the emphasis its stages carry. Every stage states the user's goal and task,
the emotion in play, the friction and trust needed, and the exit risk — all cited.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import JourneyKind, JourneyPhase, Severity

__all__ = ["InvalidJourneyError", "JourneyStage", "UXJourney"]


class InvalidJourneyError(DesignDirectorError):
    """Raised when a journey is constructed with invalid data (e.g. duplicate phase)."""

    code = "invalid_ux_journey"
    http_status = 422


@dataclass(frozen=True, slots=True)
class JourneyStage:
    """One phase of a UX journey.

    Attributes:
        phase: The journey phase this stage covers.
        user_goal: What the user is trying to do here.
        task: The concrete task the stage supports.
        emotion: The dominant emotion in play (from the psychology model).
        friction: The friction that surfaces here.
        trust_needed: The trust the stage must supply.
        exit_risk: How likely the user is to drop off here.
        note: An optional stage-specific note (e.g. WCAG level, mobile constraint).
        evidence_ids: The evidence supporting the stage.
    """

    phase: JourneyPhase
    user_goal: str
    task: str = ""
    emotion: str = ""
    friction: tuple[str, ...] = ()
    trust_needed: tuple[str, ...] = ()
    exit_risk: Severity = Severity(2)
    note: str = ""
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.user_goal or not self.user_goal.strip():
            raise InvalidJourneyError("JourneyStage.user_goal must be non-empty.")
        object.__setattr__(self, "friction", tuple(self.friction))
        object.__setattr__(self, "trust_needed", tuple(self.trust_needed))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


_PHASE_ORDER = {phase: index for index, phase in enumerate(JourneyPhase)}


@dataclass(frozen=True, slots=True)
class UXJourney:
    """A typed, ordered, cited UX journey."""

    kind: JourneyKind
    stages: tuple[JourneyStage, ...] = ()

    def __post_init__(self) -> None:
        stages = tuple(self.stages)
        seen: set[JourneyPhase] = set()
        for stage in stages:
            if stage.phase in seen:
                raise InvalidJourneyError(
                    "UXJourney has duplicate phase.",
                    details={"kind": self.kind.value, "phase": stage.phase.value},
                )
            seen.add(stage.phase)
        object.__setattr__(
            self, "stages", tuple(sorted(stages, key=lambda s: _PHASE_ORDER[s.phase]))
        )

    @classmethod
    def of(cls, kind: JourneyKind, stages: Iterable[JourneyStage]) -> UXJourney:
        return cls(kind=kind, stages=tuple(stages))

    def __len__(self) -> int:
        return len(self.stages)

    def __iter__(self):
        return iter(self.stages)

    def stage(self, phase: JourneyPhase) -> JourneyStage | None:
        return next((s for s in self.stages if s.phase is phase), None)

    def highest_exit_risk(self) -> JourneyStage | None:
        return max(self.stages, key=lambda s: int(s.exit_risk), default=None)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for s in self.stages for eid in s.evidence_ids)
