"""Strongly-typed identifiers for the Design Language Engine.

Every addressable thing the engine defines — a design-language specification and its stable
lineage, the cited evidence it rests on, the philosophies and rules it establishes, the visual
constraints it enforces, and the nodes and edges of the two visual/language graphs — is
referenced by a *typed* identifier rather than a bare :class:`uuid.UUID` or :class:`str`. As
across the rest of the platform, this is a deliberate Domain-Driven Design choice: distinct id
types cannot be confused for one another at type-check time *or* at runtime, all UUID
parsing/validation lives in one place, and signatures document themselves.

Two ids encode the versioning model (immutable, versioned specifications, consistent with
Phases 3–13):

* :class:`DesignLanguageSpecLineageId` — the stable lineage identity of a specification,
  constant across every re-run version.
* :class:`DesignLanguageSpecId` — the identity of one immutable specification version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers.

Testing considerations
----------------------
* ``DesignLanguageSpecId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``DLNodeId(u) != RuleId(u)``) and hash to separate
  dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidDLIdError` on malformed
  input, ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "ConstraintId",
    "DLEdgeId",
    "DLEvidenceId",
    "DLNodeId",
    "DesignLanguageSpecId",
    "DesignLanguageSpecLineageId",
    "Identifier",
    "InvalidDLIdError",
    "PhilosophyId",
    "RuleId",
]


class InvalidDLIdError(DesignDirectorError):
    """Raised when a value cannot form a valid Design Language identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the API
    layer can translate it uniformly, while remaining specific enough for the domain and tests
    to branch on.
    """

    code = "invalid_design_language_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all Design Language identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`DesignLanguageSpecId`, :class:`RuleId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidDLIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. DesignLanguageSpecId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidDLIdError(
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
            InvalidDLIdError: If ``raw`` is not a well-formed UUID string (including ``None``
                or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidDLIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidDLIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DesignLanguageSpecLineageId(Identifier):
    """The stable lineage identity of a specification, constant across every version."""


@dataclass(frozen=True, slots=True)
class DesignLanguageSpecId(Identifier):
    """The identity of one immutable version of a design-language specification."""


@dataclass(frozen=True, slots=True)
class DLEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class PhilosophyId(Identifier):
    """Identifies a design philosophy within the specification."""


@dataclass(frozen=True, slots=True)
class RuleId(Identifier):
    """Identifies a consistency or composition rule."""


@dataclass(frozen=True, slots=True)
class ConstraintId(Identifier):
    """Identifies a visual constraint."""


@dataclass(frozen=True, slots=True)
class DLNodeId(Identifier):
    """Identifies a node in one of the two design-language graphs."""


@dataclass(frozen=True, slots=True)
class DLEdgeId(Identifier):
    """Identifies a typed edge between two design-language-graph nodes."""
