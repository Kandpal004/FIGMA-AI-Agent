"""Visibility rules — when a component is shown or hidden.

A :class:`VisibilityRule` governs when a component is visible (always, mobile-only,
desktop-only, conditional, hidden) and under what condition. The :class:`VisibilityRuleSet` is
the immutable collection. These encode intelligence like "Sticky Add-To-Cart shows on mobile
below the fold" or "Announcement Bar is hidden at checkout".

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId, RuleId
from component_intelligence.domain.shared.value_objects import ComponentType, VisibilityKind

__all__ = ["InvalidVisibilityError", "VisibilityRule", "VisibilityRuleSet"]


class InvalidVisibilityError(DesignDirectorError):
    """Raised when a visibility rule or set is constructed with invalid data."""

    code = "invalid_component_intelligence_visibility"
    http_status = 422


@dataclass(frozen=True, slots=True)
class VisibilityRule:
    """When a component is visible.

    Attributes:
        id: Rule identity.
        component: The component the rule governs.
        kind: The visibility posture.
        condition: The condition under which it applies.
        evidence_ids: The evidence grounding it.
    """

    id: RuleId
    component: ComponentType
    kind: VisibilityKind
    condition: str = ""
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class VisibilityRuleSet:
    """The immutable set of visibility rules."""

    rules: tuple[VisibilityRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[VisibilityRule]) -> VisibilityRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def for_component(self, component: ComponentType) -> tuple[VisibilityRule, ...]:
        return tuple(r for r in self.rules if r.component is component)

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.all_evidence_ids())
