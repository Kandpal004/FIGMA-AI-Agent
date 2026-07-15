"""Strongly-typed identifiers for the Component Intelligence Engine.

Every addressable thing the engine reasons about — a composition specification and its stable
lineage, the cited evidence it rests on, the per-component decisions it makes, the composition/
placement/visibility/reuse rules it derives, the compatibility links between components, and
the nodes and edges of the two graphs — is referenced by a *typed* identifier rather than a
bare :class:`uuid.UUID` or :class:`str`. As across the rest of the platform, this is a
deliberate Domain-Driven Design choice: distinct id types cannot be confused for one another
at type-check time *or* at runtime, all UUID parsing/validation lives in one place, and
signatures document themselves.

Two ids encode the versioning model (immutable, versioned specifications, consistent with
Phases 3–14):

* :class:`ComponentSpecLineageId` — the stable lineage identity of a specification, constant
  across every re-run version.
* :class:`ComponentSpecId` — the identity of one immutable specification version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers.

Testing considerations
----------------------
* ``ComponentSpecId.new()`` yields distinct instances; different concrete id types wrapping the
  same UUID are not equal (``CINodeId(u) != DecisionId(u)``) and hash to separate keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidCIIdError` on malformed
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
    "CIEdgeId",
    "CIEvidenceId",
    "CINodeId",
    "CompatibilityId",
    "ComponentSpecId",
    "ComponentSpecLineageId",
    "DecisionId",
    "Identifier",
    "InvalidCIIdError",
    "RuleId",
]


class InvalidCIIdError(DesignDirectorError):
    """Raised when a value cannot form a valid Component Intelligence identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the API
    layer can translate it uniformly, while remaining specific enough for the domain and tests
    to branch on.
    """

    code = "invalid_component_intelligence_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all Component Intelligence identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`ComponentSpecId`, :class:`DecisionId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidCIIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. ComponentSpecId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidCIIdError(
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
            InvalidCIIdError: If ``raw`` is not a well-formed UUID string (including ``None`` or
                a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidCIIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidCIIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ComponentSpecLineageId(Identifier):
    """The stable lineage identity of a specification, constant across every version."""


@dataclass(frozen=True, slots=True)
class ComponentSpecId(Identifier):
    """The identity of one immutable version of a component-composition specification."""


@dataclass(frozen=True, slots=True)
class CIEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class DecisionId(Identifier):
    """Identifies a per-component decision."""


@dataclass(frozen=True, slots=True)
class RuleId(Identifier):
    """Identifies a composition/placement/visibility/responsive/reuse rule."""


@dataclass(frozen=True, slots=True)
class CompatibilityId(Identifier):
    """Identifies a compatibility link between two components."""


@dataclass(frozen=True, slots=True)
class CINodeId(Identifier):
    """Identifies a node in one of the two component graphs."""


@dataclass(frozen=True, slots=True)
class CIEdgeId(Identifier):
    """Identifies a typed edge between two component-graph nodes."""
