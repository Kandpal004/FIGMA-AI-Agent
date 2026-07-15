"""Composition rules — how components combine into a page.

A :class:`CompositionRule` governs how components combine (order, grouping, hierarchy,
density). The :class:`CompositionRuleSet` is the immutable collection. These are the rules a
future layout must obey to compose the components coherently.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId, RuleId
from component_intelligence.domain.shared.value_objects import CompositionRuleKind

__all__ = ["CompositionRule", "CompositionRuleSet", "InvalidCompositionRuleError"]


class InvalidCompositionRuleError(DesignDirectorError):
    """Raised when a composition rule or set is constructed with invalid data."""

    code = "invalid_component_intelligence_composition_rule"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CompositionRule:
    """One rule for how components combine into a page.

    Attributes:
        id: Rule identity.
        kind: The dimension it governs.
        statement: The rule, phrased so it can be applied.
        evidence_ids: The evidence grounding it.
    """

    id: RuleId
    kind: CompositionRuleKind
    statement: str
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidCompositionRuleError("CompositionRule.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class CompositionRuleSet:
    """The immutable set of composition rules."""

    rules: tuple[CompositionRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[CompositionRule]) -> CompositionRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def by_kind(self, kind: CompositionRuleKind) -> tuple[CompositionRule, ...]:
        return tuple(r for r in self.rules if r.kind is kind)

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.all_evidence_ids())
