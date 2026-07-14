"""Retention strategy — how the brand keeps and grows customers.

A :class:`RetentionStrategy` names the :class:`RetentionLever` s the brand pulls after
the first purchase and the lifecycle focus. Cited, like everything else.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import Priority, RetentionLeverKind

__all__ = ["InvalidRetentionError", "RetentionLever", "RetentionStrategy"]


class InvalidRetentionError(DesignDirectorError):
    """Raised when retention strategy is constructed with invalid data."""

    code = "invalid_retention_strategy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class RetentionLever:
    """One cited retention lever.

    Attributes:
        kind: The kind of lever.
        rationale: Why it fits this brand and customer.
        priority: Its priority relative to other levers.
        evidence_ids: The evidence supporting it.
    """

    kind: RetentionLeverKind
    rationale: str
    priority: Priority
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise InvalidRetentionError("RetentionLever.rationale must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class RetentionStrategy:
    """The complete, cited retention strategy."""

    levers: tuple[RetentionLever, ...] = ()
    lifecycle_focus: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "levers", tuple(self.levers))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def by_priority(self) -> tuple[RetentionLever, ...]:
        return tuple(sorted(self.levers, key=lambda x: int(x.priority), reverse=True))

    def all_evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (*self.evidence_ids, *(eid for x in self.levers for eid in x.evidence_ids))
