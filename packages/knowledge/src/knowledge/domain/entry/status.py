"""The knowledge lifecycle: statuses and their legal transitions.

Because the Knowledge Engine is meant to be *the source of truth*, entries cannot
simply appear — they are curated through a governed lifecycle, and only ``ACTIVE``
knowledge is served to reasoning by default. This module defines the six lifecycle
states and a strict, self-verifying transition machine (the same discipline as the
Phase-2 step-state machine): illegal transitions raise a domain exception, the
table is deterministic, and its integrity is checkable by a test.

The lifecycle::

    DRAFT ──propose──► PROPOSED ──validate──► ACTIVE ──deprecate──► DEPRECATED
      ▲                   │ reject               │ supersede            │
      └───────────────────┘                      ▼                      │
                                            SUPERSEDED ─────────────────┤
                                                                        ▼
                                    (any non-archived) ────────────► ARCHIVED

``ARCHIVED`` is terminal; a ``DEPRECATED`` entry may be reinstated to ``ACTIVE``.

Pure domain: no I/O, no mutable global state (the table is an immutable constant).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from core.errors import DesignDirectorError

__all__ = [
    "ACTIVE_STATUSES",
    "LEGAL_STATUS_TRANSITIONS",
    "IllegalStatusTransitionError",
    "KnowledgeStatus",
    "KnowledgeStatusMachine",
    "StatusMachineIntegrityError",
    "StatusTransition",
]


class KnowledgeStatus(str, Enum):
    """The lifecycle state of a knowledge entry version.

    * ``DRAFT``      — authored, not yet submitted.
    * ``PROPOSED``   — submitted, awaiting the curation/validation gate.
    * ``ACTIVE``     — validated and served to reasoning (the default query set).
    * ``DEPRECATED`` — still true but no longer recommended; excluded by default.
    * ``SUPERSEDED`` — replaced by a newer version of the same lineage.
    * ``ARCHIVED``   — retained for history only; terminal.
    """

    DRAFT = "draft"
    PROPOSED = "proposed"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"

    @property
    def is_terminal(self) -> bool:
        """Whether no further transition is possible from this status."""
        return self is KnowledgeStatus.ARCHIVED

    @property
    def is_servable(self) -> bool:
        """Whether reasoning serves this status by default (only ``ACTIVE``)."""
        return self in ACTIVE_STATUSES


#: Statuses served to reasoning by default.
ACTIVE_STATUSES: frozenset[KnowledgeStatus] = frozenset({KnowledgeStatus.ACTIVE})


class IllegalStatusTransitionError(DesignDirectorError):
    """Raised when a knowledge status transition is not permitted."""

    code = "illegal_status_transition"
    http_status = 409

    def __init__(self, source: KnowledgeStatus, target: KnowledgeStatus) -> None:
        self.source = source
        self.target = target
        super().__init__(
            f"Illegal knowledge status transition: {source.value} -> {target.value}.",
            details={
                "source": source.value,
                "target": target.value,
                "allowed": sorted(s.value for s in _STATUS_TABLE[source]),
            },
        )


class StatusMachineIntegrityError(DesignDirectorError):
    """Raised by :meth:`KnowledgeStatusMachine.verify_integrity` on an
    inconsistent table (a programming error, not a runtime condition)."""

    code = "status_machine_integrity"
    http_status = 500


_STATUS_TABLE: dict[KnowledgeStatus, frozenset[KnowledgeStatus]] = {
    KnowledgeStatus.DRAFT: frozenset({KnowledgeStatus.PROPOSED, KnowledgeStatus.ARCHIVED}),
    KnowledgeStatus.PROPOSED: frozenset(
        {KnowledgeStatus.ACTIVE, KnowledgeStatus.DRAFT, KnowledgeStatus.ARCHIVED}
    ),
    KnowledgeStatus.ACTIVE: frozenset(
        {KnowledgeStatus.DEPRECATED, KnowledgeStatus.SUPERSEDED, KnowledgeStatus.ARCHIVED}
    ),
    KnowledgeStatus.DEPRECATED: frozenset(
        {KnowledgeStatus.ACTIVE, KnowledgeStatus.ARCHIVED}
    ),
    KnowledgeStatus.SUPERSEDED: frozenset({KnowledgeStatus.ARCHIVED}),
    KnowledgeStatus.ARCHIVED: frozenset(),
}

#: Read-only view of the canonical status-transition table.
LEGAL_STATUS_TRANSITIONS: Mapping[KnowledgeStatus, frozenset[KnowledgeStatus]] = (
    MappingProxyType(_STATUS_TABLE)
)


@dataclass(frozen=True, slots=True)
class StatusTransition:
    """An immutable, already-validated status move.

    Constructing one proves the move is legal; an illegal pair raises
    :class:`IllegalStatusTransitionError`.
    """

    source: KnowledgeStatus
    target: KnowledgeStatus

    def __post_init__(self) -> None:
        if self.target not in _STATUS_TABLE[self.source]:
            raise IllegalStatusTransitionError(self.source, self.target)


class KnowledgeStatusMachine:
    """A pure, stateless service validating knowledge status transitions."""

    def allowed(self, source: KnowledgeStatus) -> frozenset[KnowledgeStatus]:
        """States reachable from ``source`` in one transition."""
        return _STATUS_TABLE[source]

    def is_legal(self, source: KnowledgeStatus, target: KnowledgeStatus) -> bool:
        """Whether ``source -> target`` is permitted."""
        return target in _STATUS_TABLE[source]

    def validate(self, source: KnowledgeStatus, target: KnowledgeStatus) -> None:
        """Assert ``source -> target`` is legal.

        Raises:
            IllegalStatusTransitionError: If the transition is not permitted.
        """
        if not self.is_legal(source, target):
            raise IllegalStatusTransitionError(source, target)

    def transition(
        self, source: KnowledgeStatus, target: KnowledgeStatus
    ) -> StatusTransition:
        """Validate and return the move as a :class:`StatusTransition`."""
        return StatusTransition(source=source, target=target)

    @staticmethod
    def verify_integrity() -> None:
        """Prove the transition table is internally consistent.

        Checks total coverage, valid targets, no self-loops, and that exactly the
        states with no outgoing transitions are terminal (``ARCHIVED``).

        Raises:
            StatusMachineIntegrityError: If any invariant is violated.
        """
        missing = [s for s in KnowledgeStatus if s not in _STATUS_TABLE]
        if missing:
            raise StatusMachineIntegrityError(
                "Status table is missing states.",
                details={"missing": [s.value for s in missing]},
            )
        for source, targets in _STATUS_TABLE.items():
            if source in targets:
                raise StatusMachineIntegrityError(
                    "Status table contains a self-loop.", details={"state": source.value}
                )
        empty = frozenset(s for s, t in _STATUS_TABLE.items() if not t)
        expected = frozenset(s for s in KnowledgeStatus if s.is_terminal)
        if empty != expected:
            raise StatusMachineIntegrityError(
                "States with no outgoing transitions do not match terminal states.",
                details={
                    "no_outgoing": sorted(s.value for s in empty),
                    "terminal": sorted(s.value for s in expected),
                },
            )
