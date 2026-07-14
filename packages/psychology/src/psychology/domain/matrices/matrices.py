"""The nine psychology matrices, and their grouping.

Each matrix is an immutable collection of its cited cell type; :class:`PsychologyMatrices`
groups all nine (Objection, Trust, Motivation, Emotion, Behavior, Risk, Value,
Confidence, Retention) into one value object the report composes.

Pure domain: standard library and the cell models.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from psychology.domain.matrices.cells import (
    BehaviorCell,
    ConfidenceCell,
    EmotionCell,
    MotivationCell,
    ObjectionCell,
    RetentionCell,
    RiskCell,
    TrustCell,
    ValueCell,
)
from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import FeasibilityBand

__all__ = [
    "BehaviorMatrix",
    "ConfidenceMatrix",
    "EmotionMatrix",
    "MotivationMatrix",
    "ObjectionMatrix",
    "PsychologyMatrices",
    "RetentionMatrix",
    "RiskMatrix",
    "TrustMatrix",
    "ValueMatrix",
]


@dataclass(frozen=True, slots=True)
class ObjectionMatrix:
    cells: tuple[ObjectionCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[ObjectionCell]) -> ObjectionMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class TrustMatrix:
    cells: tuple[TrustCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[TrustCell]) -> TrustMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class MotivationMatrix:
    cells: tuple[MotivationCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[MotivationCell]) -> MotivationMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class EmotionMatrix:
    cells: tuple[EmotionCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[EmotionCell]) -> EmotionMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class BehaviorMatrix:
    cells: tuple[BehaviorCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[BehaviorCell]) -> BehaviorMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def feasible(self) -> tuple[BehaviorCell, ...]:
        """Behaviors the Fogg model rates as likely to happen."""
        return tuple(c for c in self.cells if c.feasibility is FeasibilityBand.LIKELY)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class RiskMatrix:
    cells: tuple[RiskCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[RiskCell]) -> RiskMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def by_severity(self) -> tuple[RiskCell, ...]:
        return tuple(sorted(self.cells, key=lambda c: c.severity, reverse=True))

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class ValueMatrix:
    cells: tuple[ValueCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[ValueCell]) -> ValueMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class ConfidenceMatrix:
    cells: tuple[ConfidenceCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[ConfidenceCell]) -> ConfidenceMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class RetentionMatrix:
    cells: tuple[RetentionCell, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))

    @classmethod
    def of(cls, cells: Iterable[RetentionCell]) -> RetentionMatrix:
        return cls(cells=tuple(cells))

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for c in self.cells for eid in c.evidence_ids)


@dataclass(frozen=True, slots=True)
class PsychologyMatrices:
    """The nine psychology matrices, grouped."""

    objection: ObjectionMatrix = ObjectionMatrix()
    trust: TrustMatrix = TrustMatrix()
    motivation: MotivationMatrix = MotivationMatrix()
    emotion: EmotionMatrix = EmotionMatrix()
    behavior: BehaviorMatrix = BehaviorMatrix()
    risk: RiskMatrix = RiskMatrix()
    value: ValueMatrix = ValueMatrix()
    confidence: ConfidenceMatrix = ConfidenceMatrix()
    retention: RetentionMatrix = RetentionMatrix()

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return (
            *self.objection.evidence_ids(),
            *self.trust.evidence_ids(),
            *self.motivation.evidence_ids(),
            *self.emotion.evidence_ids(),
            *self.behavior.evidence_ids(),
            *self.risk.evidence_ids(),
            *self.value.evidence_ids(),
            *self.confidence.evidence_ids(),
            *self.retention.evidence_ids(),
        )

    def count(self) -> int:
        return (
            len(self.objection) + len(self.trust) + len(self.motivation)
            + len(self.emotion) + len(self.behavior) + len(self.risk)
            + len(self.value) + len(self.confidence) + len(self.retention)
        )
