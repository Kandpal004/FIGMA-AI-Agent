"""Strongly-typed identifiers for the Knowledge Engine.

Every addressable thing in the knowledge corpus is referenced by a *typed*
identifier rather than a bare :class:`uuid.UUID` or :class:`str`. As in the rest
of the platform, this is a deliberate Domain-Driven Design choice: distinct id
types cannot be confused for one another at type-check time *or* at runtime, all
UUID parsing/validation happens in exactly one place, and signatures document
themselves (``get_active(knowledge_id: KnowledgeId)`` says far more than
``get_active(uuid: UUID)``).

The two most important ids here encode the approved versioning model:

* :class:`KnowledgeId` — the **stable lineage** identity of a piece of
  knowledge. It never changes across re-versioning, so relationships between
  entries always point at a :class:`KnowledgeId` and survive new versions.
* :class:`EntryVersionId` — the identity of one **immutable version** of a
  knowledge entry. Every edit mints a new :class:`EntryVersionId` under the same
  :class:`KnowledgeId`.

This module depends only on the standard library and the shared-kernel error
base (:mod:`core.errors`); it imports nothing from the application or
infrastructure layers, keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``KnowledgeId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``KnowledgeId(u) != EntryVersionId(u)``)
  and hash to separate dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises
  :class:`InvalidKnowledgeIdError` on malformed input, ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "EntryVersionId",
    "Identifier",
    "InvalidKnowledgeIdError",
    "KnowledgeId",
    "ReferenceId",
    "RelationId",
]


class InvalidKnowledgeIdError(DesignDirectorError):
    """Raised when a value cannot form a valid knowledge identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to
    branch on.
    """

    code = "invalid_knowledge_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all knowledge identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete
    subclasses (:class:`KnowledgeId`, :class:`EntryVersionId`, …). Direct
    instantiation is rejected so an untyped identifier can never enter the
    domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidKnowledgeIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. KnowledgeId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidKnowledgeIdError(
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
            InvalidKnowledgeIdError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidKnowledgeIdError(
                f"{cls.__name__}.from_string expects a str, got "
                f"{type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidKnowledgeIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class KnowledgeId(Identifier):
    """The stable lineage identity of a piece of knowledge.

    Constant across every version of an entry. All relationships between entries
    reference a :class:`KnowledgeId` (never a version), so the knowledge graph
    remains intact when an entry is re-versioned."""


@dataclass(frozen=True, slots=True)
class EntryVersionId(Identifier):
    """The identity of one immutable version of a knowledge entry.

    A fresh :class:`EntryVersionId` is minted for every new version created under
    a given :class:`KnowledgeId`."""


@dataclass(frozen=True, slots=True)
class RelationId(Identifier):
    """Identifies a single typed relationship (edge) between two entries."""


@dataclass(frozen=True, slots=True)
class ReferenceId(Identifier):
    """Identifies a single citation/reference attached to an entry."""
