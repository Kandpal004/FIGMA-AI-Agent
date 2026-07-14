"""Strongly-typed identifiers for the Business Strategy Engine.

Every addressable thing the engine works with — a strategy report and its stable
lineage, the cited evidence it rests on, the strategic decisions it makes, and the
components those decisions connect — is referenced by a *typed* identifier rather
than a bare :class:`uuid.UUID` or :class:`str`. As across the rest of the platform,
this is a deliberate Domain-Driven Design choice: distinct id types cannot be
confused for one another at type-check time *or* at runtime, all UUID
parsing/validation lives in one place, and signatures document themselves.

This matters especially here because the decision graph cross-references constantly —
a :class:`DecisionEdgeId` links two :class:`StrategicDecisionId` s, every decision
cites :class:`StrategyEvidenceId` s, and every prioritized item, risk, and
opportunity traces back to a decision and its evidence. Typing those references makes
an accidental mix a compile error, not a silent graph corruption.

Two ids encode the versioning model (immutable, versioned reports, consistent with
Phases 3–6):

* :class:`StrategyReportLineageId` — the stable lineage identity of a report,
  constant across every re-run version.
* :class:`StrategyReportId` — the identity of one immutable report version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure
layers, keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``StrategyReportId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``StrategicDecisionId(u) != PersonaId(u)``)
  and hash to separate dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidStrategyIdError`
  on malformed input, ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "BusinessGoalId",
    "BusinessOpportunityId",
    "BusinessRiskId",
    "CustomerPersonaId",
    "DecisionEdgeId",
    "Identifier",
    "InvalidStrategyIdError",
    "JobToBeDoneId",
    "MessagingPillarId",
    "PrioritizedItemId",
    "RevenueOpportunityId",
    "StrategicDecisionId",
    "StrategyComponentId",
    "StrategyEdgeId",
    "StrategyEvidenceId",
    "StrategyReportId",
    "StrategyReportLineageId",
    "TrustElementId",
]


class InvalidStrategyIdError(DesignDirectorError):
    """Raised when a value cannot form a valid strategy identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to branch
    on.
    """

    code = "invalid_strategy_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all strategy identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete
    subclasses (:class:`StrategyReportId`, :class:`StrategicDecisionId`, …). Direct
    instantiation is rejected so an untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidStrategyIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. StrategyReportId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidStrategyIdError(
                f"{type(self).__name__} requires a uuid.UUID, got "
                f"{type(self.value).__name__}.",
                details={"identifier_type": type(self).__name__},
            )

    @classmethod
    def new(cls) -> Self:
        """Generate a fresh, random identifier (UUID version 4)."""
        return cls(uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Self:
        """Parse an identifier from its canonical string form.

        Args:
            raw: A UUID string, typically produced by ``str(identifier)``.

        Returns:
            The parsed identifier of the concrete type this is called on.

        Raises:
            InvalidStrategyIdError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidStrategyIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidStrategyIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class StrategyReportLineageId(Identifier):
    """The stable lineage identity of a strategy report, constant across every
    re-run version."""


@dataclass(frozen=True, slots=True)
class StrategyReportId(Identifier):
    """The identity of one immutable version of a strategy report."""


@dataclass(frozen=True, slots=True)
class StrategyEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class BusinessGoalId(Identifier):
    """Identifies a business goal."""


@dataclass(frozen=True, slots=True)
class CustomerPersonaId(Identifier):
    """Identifies a customer persona."""


@dataclass(frozen=True, slots=True)
class JobToBeDoneId(Identifier):
    """Identifies a job-to-be-done."""


@dataclass(frozen=True, slots=True)
class MessagingPillarId(Identifier):
    """Identifies a messaging pillar."""


@dataclass(frozen=True, slots=True)
class TrustElementId(Identifier):
    """Identifies a required trust element."""


@dataclass(frozen=True, slots=True)
class StrategicDecisionId(Identifier):
    """Identifies a strategic decision (a node in the decision graph)."""


@dataclass(frozen=True, slots=True)
class DecisionEdgeId(Identifier):
    """Identifies a typed edge between two strategic decisions."""


@dataclass(frozen=True, slots=True)
class StrategyComponentId(Identifier):
    """Identifies a component (pillar) in the strategy graph."""


@dataclass(frozen=True, slots=True)
class StrategyEdgeId(Identifier):
    """Identifies a typed edge between two strategy components."""


@dataclass(frozen=True, slots=True)
class PrioritizedItemId(Identifier):
    """Identifies an item on the priority matrix."""


@dataclass(frozen=True, slots=True)
class BusinessRiskId(Identifier):
    """Identifies a business risk."""


@dataclass(frozen=True, slots=True)
class BusinessOpportunityId(Identifier):
    """Identifies a business opportunity."""


@dataclass(frozen=True, slots=True)
class RevenueOpportunityId(Identifier):
    """Identifies a revenue opportunity."""
