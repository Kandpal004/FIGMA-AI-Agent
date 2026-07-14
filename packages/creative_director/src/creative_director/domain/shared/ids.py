"""Strongly-typed identifiers for the Creative Director Engine.

Every addressable thing the engine rules on — a review and its stable lineage, the cited
evidence it rests on, the findings and required changes it raises, the per-dimension reviews
it produces, the approval decisions it records, and the nodes and edges of the five review
graphs — is referenced by a *typed* identifier rather than a bare :class:`uuid.UUID` or
:class:`str`. As across the rest of the platform, this is a deliberate Domain-Driven Design
choice: distinct id types cannot be confused for one another at type-check time *or* at
runtime, all UUID parsing/validation lives in one place, and signatures document themselves.

This matters especially here because the Creative Director is the platform's final authority:
an approval must be traceable to the exact findings, scores, and decisions that produced it.
A :class:`CDEdgeId` links two :class:`CDNodeId` s; every finding and change cites
:class:`CDEvidenceId` s; every decision is a :class:`DecisionId`. Typing those references
makes an accidental mix a compile error, not a silent corruption of the audit trail.

Two ids encode the versioning model (immutable, versioned reviews, consistent with Phases
3–12):

* :class:`CreativeDirectorReviewLineageId` — the stable lineage identity of a review,
  constant across every re-review, override, or committee version.
* :class:`CreativeDirectorReviewId` — the identity of one immutable review version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers.

Testing considerations
----------------------
* ``CreativeDirectorReviewId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``CDNodeId(u) != FindingId(u)``) and hash to separate
  dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidCDIdError` on malformed
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
    "CDEdgeId",
    "CDEvidenceId",
    "CDNodeId",
    "CreativeDirectorReviewId",
    "CreativeDirectorReviewLineageId",
    "DecisionId",
    "DimensionReviewId",
    "FindingId",
    "Identifier",
    "InvalidCDIdError",
    "RequiredChangeId",
]


class InvalidCDIdError(DesignDirectorError):
    """Raised when a value cannot form a valid Creative Director identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the API
    layer can translate it uniformly, while remaining specific enough for the domain and
    tests to branch on.
    """

    code = "invalid_creative_director_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all Creative Director identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`CreativeDirectorReviewId`, :class:`FindingId`, …). Direct instantiation is
    rejected so an untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidCDIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. CreativeDirectorReviewId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidCDIdError(
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
            InvalidCDIdError: If ``raw`` is not a well-formed UUID string (including ``None``
                or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidCDIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidCDIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class CreativeDirectorReviewLineageId(Identifier):
    """The stable lineage identity of a review, constant across every re-review version."""


@dataclass(frozen=True, slots=True)
class CreativeDirectorReviewId(Identifier):
    """The identity of one immutable version of a Creative Director review."""


@dataclass(frozen=True, slots=True)
class CDEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class FindingId(Identifier):
    """Identifies a single review finding."""


@dataclass(frozen=True, slots=True)
class RequiredChangeId(Identifier):
    """Identifies a required change the review demands."""


@dataclass(frozen=True, slots=True)
class DimensionReviewId(Identifier):
    """Identifies a per-dimension review verdict."""


@dataclass(frozen=True, slots=True)
class DecisionId(Identifier):
    """Identifies an approval decision in the decision history."""


@dataclass(frozen=True, slots=True)
class CDNodeId(Identifier):
    """Identifies a node in one of the five review graphs."""


@dataclass(frozen=True, slots=True)
class CDEdgeId(Identifier):
    """Identifies a typed edge between two review-graph nodes."""
