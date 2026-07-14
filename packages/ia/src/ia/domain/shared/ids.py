"""Strongly-typed identifiers for the Information Architecture Engine.

Every addressable thing the engine works with — an IA report and its stable lineage, the
cited evidence it rests on, the pages and sections it defines, the navigation items and
page relationships it produces, and the nodes of the six IA graphs — is referenced by a
*typed* identifier rather than a bare :class:`uuid.UUID` or :class:`str`. As across the
rest of the platform, this is a deliberate Domain-Driven Design choice: distinct id types
cannot be confused for one another at type-check time *or* at runtime, all UUID
parsing/validation lives in one place, and signatures document themselves.

This matters especially here because the IA graphs cross-reference constantly — an
:class:`IAEdgeId` links two :class:`IANodeId` s, every page/section cites
:class:`IAEvidenceId` s, and every navigation item and relationship traces back to a page
and its evidence. Typing those references makes an accidental mix a compile error, not a
silent structural corruption.

Two ids encode the versioning model (immutable, versioned reports, consistent with Phases
3–10):

* :class:`IAReportLineageId` — the stable lineage identity of a report, constant across
  every re-run version.
* :class:`IAReportId` — the identity of one immutable report version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers,
keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``IAReportId.new()`` yields distinct instances; different concrete id types wrapping the
  same UUID are not equal (``IANodeId(u) != PageBlueprintId(u)``) and hash to separate
  dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidIAIdError` on malformed
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
    "ContentBlockId",
    "IAEdgeId",
    "IAEvidenceId",
    "IANodeId",
    "IAReportId",
    "IAReportLineageId",
    "Identifier",
    "InvalidIAIdError",
    "NavItemId",
    "PageActionId",
    "PageBlueprintId",
    "PageRelationshipId",
    "SectionId",
]


class InvalidIAIdError(DesignDirectorError):
    """Raised when a value cannot form a valid IA identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it uniformly,
    while remaining specific enough for the domain and tests to branch on.
    """

    code = "invalid_ia_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all IA identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`IAReportId`, :class:`IANodeId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidIAIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. IAReportId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidIAIdError(
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
            InvalidIAIdError: If ``raw`` is not a well-formed UUID string (including
                ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidIAIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidIAIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class IAReportLineageId(Identifier):
    """The stable lineage identity of an IA report, constant across every re-run
    version."""


@dataclass(frozen=True, slots=True)
class IAReportId(Identifier):
    """The identity of one immutable version of an IA report."""


@dataclass(frozen=True, slots=True)
class IAEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class PageBlueprintId(Identifier):
    """Identifies a page blueprint."""


@dataclass(frozen=True, slots=True)
class SectionId(Identifier):
    """Identifies a page section."""


@dataclass(frozen=True, slots=True)
class ContentBlockId(Identifier):
    """Identifies a content block within a section."""


@dataclass(frozen=True, slots=True)
class PageActionId(Identifier):
    """Identifies a page action (primary/secondary)."""


@dataclass(frozen=True, slots=True)
class NavItemId(Identifier):
    """Identifies a navigation item."""


@dataclass(frozen=True, slots=True)
class PageRelationshipId(Identifier):
    """Identifies a relationship between two pages."""


@dataclass(frozen=True, slots=True)
class IANodeId(Identifier):
    """Identifies a node in one of the IA graphs."""


@dataclass(frozen=True, slots=True)
class IAEdgeId(Identifier):
    """Identifies a typed edge between two IA-graph nodes."""
