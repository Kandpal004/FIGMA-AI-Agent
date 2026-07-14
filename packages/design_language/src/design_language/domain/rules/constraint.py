"""Visual constraints — the hard boundaries that guard restraint and timelessness.

A :class:`VisualConstraint` is a hard boundary the visual language must not cross: a limit on
accent hues or decoration, a floor on spacing or contrast, a ceiling on motion, an explicit
avoidance of trends, or a ban on generic patterns. These are the engine's teeth against the
AI-generated look — reasoned discipline, each grounded in evidence, that keeps the language
timeless and premium. The :class:`ConstraintSet` is the immutable collection.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import ConstraintId, DLEvidenceId
from design_language.domain.shared.value_objects import ConstraintKind

__all__ = ["ConstraintSet", "InvalidConstraintError", "VisualConstraint"]


class InvalidConstraintError(DesignDirectorError):
    """Raised when a visual constraint or set is constructed with invalid data."""

    code = "invalid_design_language_constraint"
    http_status = 422


@dataclass(frozen=True, slots=True)
class VisualConstraint:
    """A hard boundary that guards restraint and timelessness.

    Attributes:
        id: Constraint identity.
        kind: The kind of boundary.
        statement: The boundary, phrased so it can be enforced.
        boundary: The concrete limit (e.g. "at most 1 accent hue").
        rationale: Why the boundary exists.
        evidence_ids: The evidence grounding it.
    """

    id: ConstraintId
    kind: ConstraintKind
    statement: str
    boundary: str = ""
    rationale: str = ""
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidConstraintError("VisualConstraint.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class ConstraintSet:
    """The immutable set of the language's visual constraints."""

    constraints: tuple[VisualConstraint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))

    @classmethod
    def of(cls, constraints: Iterable[VisualConstraint]) -> ConstraintSet:
        return cls(constraints=tuple(constraints))

    def __len__(self) -> int:
        return len(self.constraints)

    def __iter__(self):
        return iter(self.constraints)

    def by_kind(self, kind: ConstraintKind) -> tuple[VisualConstraint, ...]:
        return tuple(c for c in self.constraints if c.kind is kind)

    def kinds(self) -> frozenset[ConstraintKind]:
        return frozenset(c.kind for c in self.constraints)

    def evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(eid for c in self.constraints for eid in c.all_evidence_ids())
