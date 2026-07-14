"""The DecisionHistory — the Creative Director's append-only audit trail.

Every ruling the Creative Director ever issues on a lineage is recorded as a
:class:`DecisionRecord` and kept, so the platform can always answer *"why did the Creative
Director reject this, and who overrode it?"*. The :class:`DecisionHistory` is the ordered
chain; the aggregate carries it forward across every re-review, override, and committee
version.

Pure domain: standard library, the shared-kernel error base, CD ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from creative_director.domain.shared.ids import DecisionId
from creative_director.domain.shared.value_objects import ApprovalStatus, DeciderRole

__all__ = ["DecisionHistory", "DecisionRecord", "InvalidDecisionHistoryError"]


class InvalidDecisionHistoryError(DesignDirectorError):
    """Raised when a decision history is constructed with invalid data."""

    code = "invalid_creative_director_decision_history"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """One immutable entry in the decision history.

    Attributes:
        decision_id: The decision this records.
        status: The ruling at that point.
        decided_by: Who issued it.
        decided_at: When it was issued.
        rationale: Why it was issued.
        version: The review version the decision belongs to.
    """

    decision_id: DecisionId
    status: ApprovalStatus
    decided_by: DeciderRole
    decided_at: datetime
    rationale: str
    version: int

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise InvalidDecisionHistoryError("DecisionRecord.rationale must be non-empty.")
        if self.version < 1:
            raise InvalidDecisionHistoryError(
                "DecisionRecord.version must be >= 1.", details={"version": self.version}
            )


@dataclass(frozen=True, slots=True)
class DecisionHistory:
    """The ordered, append-only chain of every ruling on a lineage."""

    records: tuple[DecisionRecord, ...] = ()

    def __post_init__(self) -> None:
        seen: set[DecisionId] = set()
        for record in self.records:
            if record.decision_id in seen:
                raise InvalidDecisionHistoryError(
                    "Duplicate decision id in history.",
                    details={"decision_id": str(record.decision_id)},
                )
            seen.add(record.decision_id)
        object.__setattr__(self, "records", tuple(self.records))

    @classmethod
    def of(cls, records: Iterable[DecisionRecord]) -> DecisionHistory:
        return cls(records=tuple(records))

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def append(self, record: DecisionRecord) -> DecisionHistory:
        """Return a new history with ``record`` appended."""
        return DecisionHistory.of((*self.records, record))

    def current(self) -> DecisionRecord | None:
        return self.records[-1] if self.records else None

    def overrides(self) -> tuple[DecisionRecord, ...]:
        return tuple(r for r in self.records if r.decided_by is not DeciderRole.SYSTEM)

    def by_role(self, role: DeciderRole) -> tuple[DecisionRecord, ...]:
        return tuple(r for r in self.records if r.decided_by is role)
