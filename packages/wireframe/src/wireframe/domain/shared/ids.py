"""Strongly-typed identifiers for the Wireframe Planning Engine.

Every addressable thing the engine plans — a wireframe plan and its stable lineage, the
cited evidence it rests on, the pages and sections it structures, the blocks and component
requirements it specifies, the approval requirements it derives, and the nodes and edges of
the six planning graphs — is referenced by a *typed* identifier rather than a bare
:class:`uuid.UUID` or :class:`str`. As across the rest of the platform, this is a deliberate
Domain-Driven Design choice: distinct id types cannot be confused for one another at
type-check time *or* at runtime, all UUID parsing/validation lives in one place, and
signatures document themselves.

This matters especially here because a wireframe plan is a dense web of cross-references —
a :class:`SectionId` names a section's parent, children, and dependencies; a
:class:`WFEdgeId` links two :class:`WFNodeId` s; every block, component, and criterion
cites :class:`WFEvidenceId` s tracing back to one of the nine upstream engines. Typing those
references makes an accidental mix a compile error, not a silent corruption of the build
plan.

Two ids encode the versioning model (immutable, versioned plans, consistent with Phases
3–11):

* :class:`WireframePlanLineageId` — the stable lineage identity of a plan, constant across
  every re-run version.
* :class:`WireframePlanId` — the identity of one immutable plan version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers,
keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``WireframePlanId.new()`` yields distinct instances; different concrete id types wrapping
  the same UUID are not equal (``WFNodeId(u) != SectionId(u)``) and hash to separate
  dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidWireframeIdError` on
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
    "ApprovalReqId",
    "BlockId",
    "ComponentReqId",
    "Identifier",
    "InvalidWireframeIdError",
    "PagePlanId",
    "SectionId",
    "WFEdgeId",
    "WFEvidenceId",
    "WFNodeId",
    "WireframePlanId",
    "WireframePlanLineageId",
]


class InvalidWireframeIdError(DesignDirectorError):
    """Raised when a value cannot form a valid wireframe-plan identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the
    API layer can translate it uniformly, while remaining specific enough for the domain and
    tests to branch on.
    """

    code = "invalid_wireframe_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all wireframe identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`WireframePlanId`, :class:`SectionId`, …). Direct instantiation is rejected so an
    untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidWireframeIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. WireframePlanId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidWireframeIdError(
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
            InvalidWireframeIdError: If ``raw`` is not a well-formed UUID string (including
                ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidWireframeIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidWireframeIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class WireframePlanLineageId(Identifier):
    """The stable lineage identity of a wireframe plan, constant across every re-run
    version."""


@dataclass(frozen=True, slots=True)
class WireframePlanId(Identifier):
    """The identity of one immutable version of a wireframe plan."""


@dataclass(frozen=True, slots=True)
class WFEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class PagePlanId(Identifier):
    """Identifies a page plan."""


@dataclass(frozen=True, slots=True)
class SectionId(Identifier):
    """Identifies a section within a page plan."""


@dataclass(frozen=True, slots=True)
class BlockId(Identifier):
    """Identifies a content/media/trust/CTA/product/… block within a section."""


@dataclass(frozen=True, slots=True)
class ComponentReqId(Identifier):
    """Identifies a component requirement within a section."""


@dataclass(frozen=True, slots=True)
class ApprovalReqId(Identifier):
    """Identifies an approval requirement in the approval plan."""


@dataclass(frozen=True, slots=True)
class WFNodeId(Identifier):
    """Identifies a node in one of the six wireframe-planning graphs."""


@dataclass(frozen=True, slots=True)
class WFEdgeId(Identifier):
    """Identifies a typed edge between two wireframe-graph nodes."""
