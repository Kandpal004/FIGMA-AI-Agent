"""Responsive rules — how the composition reflows across breakpoints.

A :class:`ResponsiveCompositionRule` governs how a component (or the composition) behaves at a
breakpoint — e.g. "Mega Menu collapses to a Navigation drawer on mobile". The
:class:`ResponsiveRuleSet` is the immutable collection.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId, RuleId
from component_intelligence.domain.shared.value_objects import (
    Breakpoint,
    ComponentType,
    ResponsiveIntent,
)

__all__ = ["InvalidResponsiveRuleError", "ResponsiveCompositionRule", "ResponsiveRuleSet"]


class InvalidResponsiveRuleError(DesignDirectorError):
    """Raised when a responsive rule or set is constructed with invalid data."""

    code = "invalid_component_intelligence_responsive_rule"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ResponsiveCompositionRule:
    """How a component behaves at a breakpoint in the composition.

    Attributes:
        id: Rule identity.
        component: The component the rule governs.
        breakpoint: The breakpoint it applies at.
        intent: The behaviour intent at that breakpoint.
        statement: The rule, phrased so it can be applied.
        evidence_ids: The evidence grounding it.
    """

    id: RuleId
    component: ComponentType
    breakpoint: Breakpoint
    intent: ResponsiveIntent
    statement: str
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidResponsiveRuleError("ResponsiveCompositionRule.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class ResponsiveRuleSet:
    """The immutable set of responsive composition rules."""

    rules: tuple[ResponsiveCompositionRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[ResponsiveCompositionRule]) -> ResponsiveRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def for_component(self, component: ComponentType) -> tuple[ResponsiveCompositionRule, ...]:
        return tuple(r for r in self.rules if r.component is component)

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.all_evidence_ids())
