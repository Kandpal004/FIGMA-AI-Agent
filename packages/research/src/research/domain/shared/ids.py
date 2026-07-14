"""Strongly-typed identifiers for the Research Engine.

Every addressable thing the engine works with — a research report and its stable
lineage, the sources it draws from, the raw artifacts it collects, the results it
produces, and the evidence, entities, and relationships within them — is referenced
by a *typed* identifier rather than a bare :class:`uuid.UUID` or :class:`str`. As
across the rest of the platform, this is a deliberate Domain-Driven Design choice:
distinct id types cannot be confused for one another at type-check time *or* at
runtime, all UUID parsing/validation lives in one place, and signatures document
themselves.

This matters especially here because evidence, entities, and relationships
cross-reference each other constantly — a :class:`RelationshipId` links two
:class:`EntityId` s, an :class:`EntityId` cites :class:`EvidenceId` s, and every
:class:`EvidenceId` traces to a :class:`ResearchSourceId`. Typing those references
makes an accidental mix a compile error, not a silent graph corruption.

Two ids encode the versioning model (immutable, versioned reports, consistent with
Phases 3–5):

* :class:`ResearchReportLineageId` — the stable lineage identity of a report,
  constant across every re-research version.
* :class:`ResearchReportId` — the identity of one immutable report version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure
layers, keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``ResearchReportId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``EntityId(u) != EvidenceId(u)``) and hash
  to separate dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises
  :class:`InvalidResearchIdError` on malformed input, ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "ArtifactId",
    "EntityId",
    "EvidenceId",
    "Identifier",
    "InvalidResearchIdError",
    "RelationshipId",
    "ResearchReportId",
    "ResearchReportLineageId",
    "ResearchResultId",
    "ResearchSourceId",
]


class InvalidResearchIdError(DesignDirectorError):
    """Raised when a value cannot form a valid research identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to branch
    on.
    """

    code = "invalid_research_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all research identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete
    subclasses (:class:`ResearchReportId`, :class:`EntityId`, …). Direct
    instantiation is rejected so an untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidResearchIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. ResearchReportId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidResearchIdError(
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
            InvalidResearchIdError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidResearchIdError(
                f"{cls.__name__}.from_string expects a str, got "
                f"{type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidResearchIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ResearchReportLineageId(Identifier):
    """The stable lineage identity of a research report, constant across every
    re-research version."""


@dataclass(frozen=True, slots=True)
class ResearchReportId(Identifier):
    """The identity of one immutable version of a research report."""


@dataclass(frozen=True, slots=True)
class ResearchSourceId(Identifier):
    """Identifies a registered research source."""


@dataclass(frozen=True, slots=True)
class ArtifactId(Identifier):
    """Identifies a raw artifact collected from a source."""


@dataclass(frozen=True, slots=True)
class ResearchResultId(Identifier):
    """Identifies a single research result within a report."""


@dataclass(frozen=True, slots=True)
class EvidenceId(Identifier):
    """Identifies a piece of provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class EntityId(Identifier):
    """Identifies an extracted entity."""


@dataclass(frozen=True, slots=True)
class RelationshipId(Identifier):
    """Identifies a typed relationship between two entities."""
