"""The ImprovementMatrix — the actionable remediation plan a rejected subject gets back.

A :class:`ImprovementMatrix` collects every :class:`RequiredChange` the review demands and
orders them by combined urgency (priority × impact), blocking changes first. It is the
concrete "here is what to fix, in what order" a phase receives when the Creative Director
withholds approval.

Pure domain: standard library and the finding model.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from creative_director.domain.finding.finding import RequiredChange

__all__ = ["ImprovementMatrix"]


@dataclass(frozen=True, slots=True)
class ImprovementMatrix:
    """The required changes, ranked into a remediation plan."""

    changes: tuple[RequiredChange, ...] = ()

    def __post_init__(self) -> None:
        ordered = sorted(
            self.changes, key=lambda c: (c.blocking, c.rank), reverse=True
        )
        object.__setattr__(self, "changes", tuple(ordered))

    @classmethod
    def of(cls, changes: Iterable[RequiredChange]) -> ImprovementMatrix:
        return cls(changes=tuple(changes))

    def __len__(self) -> int:
        return len(self.changes)

    def __iter__(self):
        return iter(self.changes)

    def blocking(self) -> tuple[RequiredChange, ...]:
        return tuple(c for c in self.changes if c.blocking)
