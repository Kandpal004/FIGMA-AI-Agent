"""Strongly-typed identifiers for the Competitor Intelligence Engine.

Every addressable thing the engine works with — an intelligence report and its
stable lineage, the competitors it profiles, the observations it ingests, the
recurring patterns it detects, the citations it pins, and the recommendations and
risks it produces — is referenced by a *typed* identifier rather than a bare
:class:`uuid.UUID` or :class:`str`. As across the rest of the platform, this is a
deliberate Domain-Driven Design choice: distinct id types cannot be confused for
one another at type-check time *or* at runtime, all UUID parsing/validation lives
in one place, and signatures document themselves.

Two ids encode the versioning model (immutable, versioned reports, consistent with
Phases 3–4):

* :class:`ReportLineageId` — the stable lineage identity of an intelligence report,
  constant across every re-analysis version.
* :class:`ReportId` — the identity of one immutable report version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure
layers, keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``ReportId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``CompetitorId(u) != ObservationId(u)``)
  and hash to separate dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises
  :class:`InvalidCompetitiveIdError` on malformed input, ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "CompetitorId",
    "EvidenceId",
    "Identifier",
    "InvalidCompetitiveIdError",
    "ObservationId",
    "PatternId",
    "ProfileId",
    "RecommendationId",
    "ReportId",
    "ReportLineageId",
    "RiskId",
]


class InvalidCompetitiveIdError(DesignDirectorError):
    """Raised when a value cannot form a valid competitive-intelligence identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to branch
    on.
    """

    code = "invalid_competitive_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all competitive-intelligence identifiers.

    A value object wrapping a UUID. Not intended to be instantiated directly;
    construct one of the concrete subclasses (:class:`ReportId`,
    :class:`CompetitorId`, …). Direct instantiation is rejected so an untyped
    identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidCompetitiveIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. ReportId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidCompetitiveIdError(
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
            InvalidCompetitiveIdError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidCompetitiveIdError(
                f"{cls.__name__}.from_string expects a str, got "
                f"{type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidCompetitiveIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ReportLineageId(Identifier):
    """The stable lineage identity of an intelligence report, constant across every
    re-analysis version."""


@dataclass(frozen=True, slots=True)
class ReportId(Identifier):
    """The identity of one immutable version of an intelligence report."""


@dataclass(frozen=True, slots=True)
class CompetitorId(Identifier):
    """Identifies a competitor the engine profiles."""


@dataclass(frozen=True, slots=True)
class ObservationId(Identifier):
    """Identifies a single structured observation ingested about a competitor."""


@dataclass(frozen=True, slots=True)
class ProfileId(Identifier):
    """Identifies a competitor's profile within a report."""


@dataclass(frozen=True, slots=True)
class PatternId(Identifier):
    """Identifies a recurring pattern detected across competitors."""


@dataclass(frozen=True, slots=True)
class EvidenceId(Identifier):
    """Identifies an :class:`EvidenceRef` — a pinned citation of a Knowledge entry
    used within a report."""


@dataclass(frozen=True, slots=True)
class RecommendationId(Identifier):
    """Identifies a recommendation produced by the engine."""


@dataclass(frozen=True, slots=True)
class RiskId(Identifier):
    """Identifies a competitive risk in the risk matrix."""
