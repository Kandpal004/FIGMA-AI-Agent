"""Strongly-typed identifiers for the Design System Engine.

Every addressable thing the engine specifies — a design-system specification and its stable
lineage, the cited evidence it rests on, the design tokens it defines, the component specs it
produces, the themes it resolves, the constraints it enforces, and the nodes and edges of the
six graphs — is referenced by a *typed* identifier rather than a bare :class:`uuid.UUID` or
:class:`str`. As across the rest of the platform, this is a deliberate Domain-Driven Design
choice: distinct id types cannot be confused for one another at type-check time *or* at runtime,
all UUID parsing/validation lives in one place, and signatures document themselves.

Two ids encode the versioning model (immutable, versioned specifications, consistent with
Phases 3–15):

* :class:`DesignSystemSpecLineageId` — the stable lineage identity of a specification, constant
  across every re-run version.
* :class:`DesignSystemSpecId` — the identity of one immutable specification version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers.

Testing considerations
----------------------
* ``DesignSystemSpecId.new()`` yields distinct instances; different concrete id types wrapping
  the same UUID are not equal (``DSNodeId(u) != TokenId(u)``) and hash to separate keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidDSIdError` on malformed
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
    "ComponentSpecId",
    "ConstraintId",
    "DSEdgeId",
    "DSEvidenceId",
    "DSNodeId",
    "DesignSystemSpecId",
    "DesignSystemSpecLineageId",
    "Identifier",
    "InvalidDSIdError",
    "ThemeId",
    "TokenId",
]


class InvalidDSIdError(DesignDirectorError):
    """Raised when a value cannot form a valid Design System identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the API
    layer can translate it uniformly, while remaining specific enough for the domain and tests
    to branch on.
    """

    code = "invalid_design_system_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all Design System identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`DesignSystemSpecId`, :class:`TokenId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidDSIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. DesignSystemSpecId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidDSIdError(
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
            InvalidDSIdError: If ``raw`` is not a well-formed UUID string (including ``None`` or
                a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidDSIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidDSIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DesignSystemSpecLineageId(Identifier):
    """The stable lineage identity of a specification, constant across every version."""


@dataclass(frozen=True, slots=True)
class DesignSystemSpecId(Identifier):
    """The identity of one immutable version of a design-system specification."""


@dataclass(frozen=True, slots=True)
class DSEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class TokenId(Identifier):
    """Identifies a design token."""


@dataclass(frozen=True, slots=True)
class ComponentSpecId(Identifier):
    """Identifies a component specification."""


@dataclass(frozen=True, slots=True)
class ThemeId(Identifier):
    """Identifies a theme."""


@dataclass(frozen=True, slots=True)
class ConstraintId(Identifier):
    """Identifies a design-system constraint."""


@dataclass(frozen=True, slots=True)
class DSNodeId(Identifier):
    """Identifies a node in one of the six design-system graphs."""


@dataclass(frozen=True, slots=True)
class DSEdgeId(Identifier):
    """Identifies a typed edge between two design-system-graph nodes."""
