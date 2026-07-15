"""Reuse rules — which components are shared across pages and must stay identical.

A :class:`ReuseRule` records that a component (Product Card, Header, Footer, …) is reused across
several pages and must remain consistent everywhere — the DRY guarantee that keeps the
composition coherent. The :class:`ReuseRuleSet` is the immutable collection.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId, RuleId
from component_intelligence.domain.shared.value_objects import ComponentType, PageType

__all__ = ["InvalidReuseError", "ReuseRule", "ReuseRuleSet"]


class InvalidReuseError(DesignDirectorError):
    """Raised when a reuse rule or set is constructed with invalid data."""

    code = "invalid_component_intelligence_reuse"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ReuseRule:
    """A component reused across pages that must stay consistent.

    Attributes:
        id: Rule identity.
        component: The reused component.
        shared_across: The pages it is shared across.
        statement: Why it must stay consistent.
        evidence_ids: The evidence grounding it.
    """

    id: RuleId
    component: ComponentType
    shared_across: tuple[PageType, ...]
    statement: str = ""
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if len(self.shared_across) < 2:
            raise InvalidReuseError(
                "ReuseRule.shared_across must span at least two pages.",
                details={"component": self.component.value},
            )
        object.__setattr__(self, "shared_across", tuple(dict.fromkeys(self.shared_across)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class ReuseRuleSet:
    """The immutable set of reuse rules."""

    rules: tuple[ReuseRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[ReuseRule]) -> ReuseRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.all_evidence_ids())
