"""Strongly-typed identifiers for the Figma Design Engine.

Every addressable thing the engine models — a Figma design model and its stable lineage, the
cited evidence it rests on, the pages and nodes of the file, the components and component sets,
the variable collections and variables and modes, the styles, and the nodes and edges of the
five graphs — is referenced by a *typed* identifier rather than a bare :class:`uuid.UUID` or
:class:`str`. As across the rest of the platform, this is a deliberate Domain-Driven Design
choice: distinct id types cannot be confused for one another at type-check time *or* at runtime,
all UUID parsing/validation lives in one place, and signatures document themselves.

Two ids encode the versioning model (immutable, versioned models, consistent with Phases 3–17):

* :class:`FigmaDesignModelLineageId` — the stable lineage identity of a model, constant across
  every re-run version.
* :class:`FigmaDesignModelId` — the identity of one immutable model version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers — and
nothing from any Figma SDK, MCP client, or HTTP library.

Testing considerations
----------------------
* ``FigmaDesignModelId.new()`` yields distinct instances; different concrete id types wrapping the
  same UUID are not equal (``FigmaNodeId(u) != VariableId(u)``) and hash to separate keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidFDIdError` on malformed input,
  ``None``, or a non-string.
* Instances are immutable (assignment raises ``FrozenInstanceError``).
* Constructing the abstract :class:`Identifier` base directly is rejected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "FDEdgeId",
    "FDEvidenceId",
    "FDNodeId",
    "FigmaComponentId",
    "FigmaComponentSetId",
    "FigmaDesignModelId",
    "FigmaDesignModelLineageId",
    "FigmaNodeId",
    "FigmaPageId",
    "Identifier",
    "InvalidFDIdError",
    "StyleId",
    "VariableCollectionId",
    "VariableId",
    "VariableModeId",
]


class InvalidFDIdError(DesignDirectorError):
    """Raised when a value cannot form a valid Figma Design identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the API
    layer can translate it uniformly, while remaining specific enough for the domain and tests to
    branch on.
    """

    code = "invalid_figma_design_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all Figma Design identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`FigmaDesignModelId`, :class:`FigmaNodeId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidFDIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. FigmaDesignModelId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidFDIdError(
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
            InvalidFDIdError: If ``raw`` is not a well-formed UUID string (including ``None`` or a
                non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidFDIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidFDIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class FigmaDesignModelLineageId(Identifier):
    """The stable lineage identity of a model, constant across every version."""


@dataclass(frozen=True, slots=True)
class FigmaDesignModelId(Identifier):
    """The identity of one immutable version of a Figma design model."""


@dataclass(frozen=True, slots=True)
class FDEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class FigmaPageId(Identifier):
    """Identifies a Figma page."""


@dataclass(frozen=True, slots=True)
class FigmaNodeId(Identifier):
    """Identifies a node in the Figma node tree."""


@dataclass(frozen=True, slots=True)
class FigmaComponentId(Identifier):
    """Identifies a single component (one variant)."""


@dataclass(frozen=True, slots=True)
class FigmaComponentSetId(Identifier):
    """Identifies a component set (a variant matrix)."""


@dataclass(frozen=True, slots=True)
class VariableCollectionId(Identifier):
    """Identifies a variable collection."""


@dataclass(frozen=True, slots=True)
class VariableId(Identifier):
    """Identifies a variable."""


@dataclass(frozen=True, slots=True)
class VariableModeId(Identifier):
    """Identifies a mode within a variable collection."""


@dataclass(frozen=True, slots=True)
class StyleId(Identifier):
    """Identifies a published style (paint / text / effect / grid)."""


@dataclass(frozen=True, slots=True)
class FDNodeId(Identifier):
    """Identifies a node in one of the five Figma graphs."""


@dataclass(frozen=True, slots=True)
class FDEdgeId(Identifier):
    """Identifies a typed edge between two Figma-graph nodes."""
