"""The Journey Map — the seven UX journeys, grouped.

:class:`JourneyMap` holds the seven required journeys — User, Task, Decision, Trust,
Conversion, Mobile, and Accessibility — each a :class:`UXJourney` of the right kind.
Grouping them keeps the report aggregate clean and lets the facade resolve a journey by
:class:`JourneyKind`.

Pure domain: standard library and the journey primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ux.domain.journey.journey import UXJourney
from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import JourneyKind

__all__ = ["JourneyMap"]


def _empty(kind: JourneyKind) -> UXJourney:
    return UXJourney(kind=kind)


@dataclass(frozen=True, slots=True)
class JourneyMap:
    """The seven UX journeys, grouped."""

    user: UXJourney = field(default_factory=lambda: _empty(JourneyKind.USER))
    task: UXJourney = field(default_factory=lambda: _empty(JourneyKind.TASK))
    decision: UXJourney = field(default_factory=lambda: _empty(JourneyKind.DECISION))
    trust: UXJourney = field(default_factory=lambda: _empty(JourneyKind.TRUST))
    conversion: UXJourney = field(default_factory=lambda: _empty(JourneyKind.CONVERSION))
    mobile: UXJourney = field(default_factory=lambda: _empty(JourneyKind.MOBILE))
    accessibility: UXJourney = field(
        default_factory=lambda: _empty(JourneyKind.ACCESSIBILITY)
    )

    def __post_init__(self) -> None:
        for name, expected in (
            ("user", JourneyKind.USER), ("task", JourneyKind.TASK),
            ("decision", JourneyKind.DECISION), ("trust", JourneyKind.TRUST),
            ("conversion", JourneyKind.CONVERSION), ("mobile", JourneyKind.MOBILE),
            ("accessibility", JourneyKind.ACCESSIBILITY),
        ):
            journey = getattr(self, name)
            if journey.kind is not expected:
                raise ValueError(f"JourneyMap.{name} must be a {expected.value} journey.")

    def get(self, kind: JourneyKind) -> UXJourney:
        return {
            JourneyKind.USER: self.user,
            JourneyKind.TASK: self.task,
            JourneyKind.DECISION: self.decision,
            JourneyKind.TRUST: self.trust,
            JourneyKind.CONVERSION: self.conversion,
            JourneyKind.MOBILE: self.mobile,
            JourneyKind.ACCESSIBILITY: self.accessibility,
        }[kind]

    def all(self) -> tuple[UXJourney, ...]:
        return (
            self.user, self.task, self.decision, self.trust,
            self.conversion, self.mobile, self.accessibility,
        )

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for j in self.all() for eid in j.evidence_ids())
