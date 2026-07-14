"""Consistency rules — the invariants the visual language holds everywhere.

A :class:`ConsistencyRule` is an invariant the language must hold across every future surface
(all spacing derives from one ramp, type follows one modular ratio, elevation uses one set of
levels, …). The :class:`ConsistencyRuleSet` is the immutable collection. Consistency is what
makes a language feel authored rather than assembled — the opposite of the AI-generated look.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId, RuleId
from design_language.domain.shared.value_objects import ConsistencyKind

__all__ = ["ConsistencyRule", "ConsistencyRuleSet", "InvalidConsistencyError"]


class InvalidConsistencyError(DesignDirectorError):
    """Raised when a consistency rule or set is constructed with invalid data."""

    code = "invalid_design_language_consistency"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ConsistencyRule:
    """One invariant the visual language must hold everywhere.

    Attributes:
        id: Rule identity.
        kind: The dimension it governs.
        statement: The invariant, phrased so it can be checked.
        applies_to: Where the invariant applies (e.g. "all surfaces").
        evidence_ids: The evidence grounding it.
    """

    id: RuleId
    kind: ConsistencyKind
    statement: str
    applies_to: str = "all surfaces"
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidConsistencyError("ConsistencyRule.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class ConsistencyRuleSet:
    """The immutable set of the language's consistency rules."""

    rules: tuple[ConsistencyRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[ConsistencyRule]) -> ConsistencyRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def by_kind(self, kind: ConsistencyKind) -> tuple[ConsistencyRule, ...]:
        return tuple(r for r in self.rules if r.kind is kind)

    def kinds(self) -> frozenset[ConsistencyKind]:
        return frozenset(r.kind for r in self.rules)

    def evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.all_evidence_ids())
