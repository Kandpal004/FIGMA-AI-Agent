"""Brand governance rules — ownership and change control for the brand.

A :class:`BrandGovernanceRule` names who owns a scope of the brand and the process for
changing it. The :class:`GovernanceRuleSet` is the immutable collection. These keep the
brand from drifting as it scales.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId, GovernanceRuleId
from brand.domain.shared.value_objects import GovernanceScope, RuleEnforcement

__all__ = [
    "BrandGovernanceRule",
    "GovernanceRuleSet",
    "InvalidGovernanceError",
]


class InvalidGovernanceError(DesignDirectorError):
    """Raised when a governance rule is constructed with invalid data."""

    code = "invalid_governance_rule"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandGovernanceRule:
    """One cited governance rule.

    Attributes:
        id: Rule identity.
        scope: The scope it governs.
        rule: The rule statement.
        owner: Who owns/approves changes in this scope.
        enforcement: How strongly it is enforced.
        evidence_ids: The evidence supporting it.
    """

    id: GovernanceRuleId
    scope: GovernanceScope
    rule: str
    owner: str = ""
    enforcement: RuleEnforcement = RuleEnforcement.MUST
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rule or not self.rule.strip():
            raise InvalidGovernanceError("BrandGovernanceRule.rule must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class GovernanceRuleSet:
    """An immutable set of governance rules."""

    rules: tuple[BrandGovernanceRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[BrandGovernanceRule]) -> GovernanceRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def by_scope(self, scope: GovernanceScope) -> tuple[BrandGovernanceRule, ...]:
        return tuple(r for r in self.rules if r.scope is scope)

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.evidence_ids)
