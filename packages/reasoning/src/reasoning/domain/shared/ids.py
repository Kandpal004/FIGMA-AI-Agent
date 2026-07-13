"""Strongly-typed identifiers for the Reasoning Engine.

Every addressable element the engine produces — a reasoning run, the design
strategy it yields, and the nodes of the reason/decision/evidence graphs plus the
risks, trade-offs, and alternatives hanging off them — is referenced by a *typed*
identifier rather than a bare :class:`uuid.UUID` or :class:`str`. As across the
rest of the platform, this is a deliberate Domain-Driven Design choice: distinct
id types cannot be confused for one another at type-check time *or* at runtime, all
UUID parsing/validation lives in one place, and signatures document themselves
(``explain(decision_id: DecisionNodeId)`` says far more than
``explain(uuid: UUID)``).

This matters especially here because the three graphs cross-reference each other
constantly — a :class:`DecisionNodeId` cites :class:`ReasonNodeId` s which cite
:class:`EvidenceId` s. Typing those references makes an accidental mix a compile
error, not a silent graph corruption.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure
layers, keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``StrategyId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``ReasonNodeId(u) != DecisionNodeId(u)``)
  and hash to separate dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises
  :class:`InvalidReasoningIdError` on malformed input, ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AlternativeId",
    "DecisionNodeId",
    "EvidenceId",
    "Identifier",
    "InvalidReasoningIdError",
    "ReasonNodeId",
    "ReasoningRunId",
    "RiskId",
    "StrategyId",
    "TradeOffId",
]


class InvalidReasoningIdError(DesignDirectorError):
    """Raised when a value cannot form a valid reasoning identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to branch
    on.
    """

    code = "invalid_reasoning_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all reasoning identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete
    subclasses (:class:`StrategyId`, :class:`DecisionNodeId`, …). Direct
    instantiation is rejected so an untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidReasoningIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. StrategyId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidReasoningIdError(
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
            InvalidReasoningIdError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidReasoningIdError(
                f"{cls.__name__}.from_string expects a str, got "
                f"{type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidReasoningIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ReasoningRunId(Identifier):
    """Identifies a single execution of the Reasoning Engine."""


@dataclass(frozen=True, slots=True)
class StrategyId(Identifier):
    """Identifies a produced :class:`DesignStrategy` aggregate."""


@dataclass(frozen=True, slots=True)
class ReasonNodeId(Identifier):
    """Identifies a node in the reason graph (one inference step)."""


@dataclass(frozen=True, slots=True)
class DecisionNodeId(Identifier):
    """Identifies a node in the decision graph (one strategic choice)."""


@dataclass(frozen=True, slots=True)
class EvidenceId(Identifier):
    """Identifies an :class:`EvidenceRef` — a pinned citation of a Knowledge
    entry used within a strategy."""


@dataclass(frozen=True, slots=True)
class RiskId(Identifier):
    """Identifies a single identified risk in the risk assessment."""


@dataclass(frozen=True, slots=True)
class TradeOffId(Identifier):
    """Identifies a recorded trade-off between competing options."""


@dataclass(frozen=True, slots=True)
class AlternativeId(Identifier):
    """Identifies an alternative strategy considered under a different stance."""
