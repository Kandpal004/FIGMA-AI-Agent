"""Strongly-typed identifiers for the UX Strategy Engine.

Every addressable thing the engine works with — a UX strategy report and its stable
lineage, the cited evidence it rests on, the pages and goals it defines, the decisions
and flow steps it produces, and the nodes of the five UX graphs — is referenced by a
*typed* identifier rather than a bare :class:`uuid.UUID` or :class:`str`. As across the
rest of the platform, this is a deliberate Domain-Driven Design choice: distinct id types
cannot be confused for one another at type-check time *or* at runtime, all UUID
parsing/validation lives in one place, and signatures document themselves.

This matters especially here because the UX graphs cross-reference constantly — a
:class:`UXEdgeId` links two :class:`UXNodeId` s, every decision cites
:class:`UXEvidenceId` s, and every page strategy traces back to goals and its evidence.
Typing those references makes an accidental mix a compile error, not a silent graph
corruption.

Two ids encode the versioning model (immutable, versioned reports, consistent with
Phases 3–9):

* :class:`UXReportLineageId` — the stable lineage identity of a report, constant across
  every re-run version.
* :class:`UXReportId` — the identity of one immutable report version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers,
keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``UXReportId.new()`` yields distinct instances; different concrete id types wrapping the
  same UUID are not equal (``UXNodeId(u) != PageStrategyId(u)``) and hash to separate
  dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidUXIdError` on
  malformed input, ``None``, or a non-string.
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
    "CallToActionId",
    "FrictionPointId",
    "Identifier",
    "InvalidUXIdError",
    "PageStrategyId",
    "SuccessMetricId",
    "UXDecisionId",
    "UXEdgeId",
    "UXEvidenceId",
    "UXNodeId",
    "UXReportId",
    "UXReportLineageId",
    "UserGoalId",
]


class InvalidUXIdError(DesignDirectorError):
    """Raised when a value cannot form a valid UX identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to branch on.
    """

    code = "invalid_ux_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all UX identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`UXReportId`, :class:`UXNodeId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidUXIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. UXReportId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidUXIdError(
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
            InvalidUXIdError: If ``raw`` is not a well-formed UUID string (including
                ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidUXIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidUXIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class UXReportLineageId(Identifier):
    """The stable lineage identity of a UX strategy report, constant across every re-run
    version."""


@dataclass(frozen=True, slots=True)
class UXReportId(Identifier):
    """The identity of one immutable version of a UX strategy report."""


@dataclass(frozen=True, slots=True)
class UXEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class UserGoalId(Identifier):
    """Identifies a user goal."""


@dataclass(frozen=True, slots=True)
class BusinessGoalId(Identifier):
    """Identifies a business goal."""


@dataclass(frozen=True, slots=True)
class PageStrategyId(Identifier):
    """Identifies a page strategy."""


@dataclass(frozen=True, slots=True)
class CallToActionId(Identifier):
    """Identifies a call to action."""


@dataclass(frozen=True, slots=True)
class SuccessMetricId(Identifier):
    """Identifies a success metric."""


@dataclass(frozen=True, slots=True)
class FrictionPointId(Identifier):
    """Identifies a friction point."""


@dataclass(frozen=True, slots=True)
class UXDecisionId(Identifier):
    """Identifies a UX decision (a node in the UX decision graph)."""


@dataclass(frozen=True, slots=True)
class UXNodeId(Identifier):
    """Identifies a node in one of the UX graphs."""


@dataclass(frozen=True, slots=True)
class UXEdgeId(Identifier):
    """Identifies a typed edge between two UX-graph nodes."""
