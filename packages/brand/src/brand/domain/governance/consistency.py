"""Brand consistency rules — the cross-element alignment the brand must keep.

A :class:`BrandConsistencyRule` guards one :class:`ConsistencyDimension` (voice, colour,
typography, …) with an enforcement level. The :class:`ConsistencyRuleSet` is the
immutable collection. These keep the brand coherent across every touchpoint.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId, ConsistencyRuleId
from brand.domain.shared.value_objects import ConsistencyDimension, RuleEnforcement

__all__ = [
    "BrandConsistencyRule",
    "ConsistencyRuleSet",
    "InvalidConsistencyError",
]


class InvalidConsistencyError(DesignDirectorError):
    """Raised when a consistency rule is constructed with invalid data."""

    code = "invalid_consistency_rule"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandConsistencyRule:
    """One cited cross-element consistency rule.

    Attributes:
        id: Rule identity.
        dimension: The dimension it guards.
        rule: The rule statement.
        enforcement: How strongly it is enforced.
        evidence_ids: The evidence supporting it.
    """

    id: ConsistencyRuleId
    dimension: ConsistencyDimension
    rule: str
    enforcement: RuleEnforcement = RuleEnforcement.MUST
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rule or not self.rule.strip():
            raise InvalidConsistencyError("BrandConsistencyRule.rule must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ConsistencyRuleSet:
    """An immutable set of consistency rules."""

    rules: tuple[BrandConsistencyRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[BrandConsistencyRule]) -> ConsistencyRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def by_dimension(
        self, dimension: ConsistencyDimension
    ) -> tuple[BrandConsistencyRule, ...]:
        return tuple(r for r in self.rules if r.dimension is dimension)

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.evidence_ids)
