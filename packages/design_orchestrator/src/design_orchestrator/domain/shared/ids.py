"""Strongly-typed identifiers for the Design Orchestrator Engine.

Every addressable thing the engine plans — a design-execution plan and its stable lineage, the
cited evidence it rests on, the per-page and per-section plans it orders, the layout regions it
places, the review checkpoints it schedules, and the nodes and edges of the execution and layout
graphs — is referenced by a *typed* identifier rather than a bare :class:`uuid.UUID` or
:class:`str`. As across the rest of the platform, this is a deliberate Domain-Driven Design
choice: distinct id types cannot be confused for one another at type-check time *or* at runtime,
all UUID parsing/validation lives in one place, and signatures document themselves.

Two ids encode the versioning model (immutable, versioned plans, consistent with Phases 3–16):

* :class:`DesignExecutionPlanLineageId` — the stable lineage identity of a plan, constant across
  every re-run version.
* :class:`DesignExecutionPlanId` — the identity of one immutable plan version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers.

Testing considerations
----------------------
* ``DesignExecutionPlanId.new()`` yields distinct instances; different concrete id types wrapping
  the same UUID are not equal (``DONodeId(u) != SectionPlanId(u)``) and hash to separate keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidDOIdError` on malformed
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
    "DOEdgeId",
    "DOEvidenceId",
    "DONodeId",
    "DesignExecutionPlanId",
    "DesignExecutionPlanLineageId",
    "Identifier",
    "InvalidDOIdError",
    "LayoutRegionId",
    "PagePlanId",
    "ReviewCheckpointId",
    "SectionPlanId",
]


class InvalidDOIdError(DesignDirectorError):
    """Raised when a value cannot form a valid Design Orchestrator identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError` so the API
    layer can translate it uniformly, while remaining specific enough for the domain and tests
    to branch on.
    """

    code = "invalid_design_orchestrator_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all Design Orchestrator identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`DesignExecutionPlanId`, :class:`SectionPlanId`, …). Direct instantiation is rejected
    so an untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidDOIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. DesignExecutionPlanId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidDOIdError(
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
            InvalidDOIdError: If ``raw`` is not a well-formed UUID string (including ``None`` or
                a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidDOIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidDOIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DesignExecutionPlanLineageId(Identifier):
    """The stable lineage identity of a plan, constant across every version."""


@dataclass(frozen=True, slots=True)
class DesignExecutionPlanId(Identifier):
    """The identity of one immutable version of a design-execution plan."""


@dataclass(frozen=True, slots=True)
class DOEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class PagePlanId(Identifier):
    """Identifies a per-page plan."""


@dataclass(frozen=True, slots=True)
class SectionPlanId(Identifier):
    """Identifies a per-section plan (the unit every mapping keys on)."""


@dataclass(frozen=True, slots=True)
class LayoutRegionId(Identifier):
    """Identifies a layout region."""


@dataclass(frozen=True, slots=True)
class ReviewCheckpointId(Identifier):
    """Identifies a scheduled review checkpoint."""


@dataclass(frozen=True, slots=True)
class DONodeId(Identifier):
    """Identifies a node in the execution or layout graph."""


@dataclass(frozen=True, slots=True)
class DOEdgeId(Identifier):
    """Identifies a typed edge between two orchestrator-graph nodes."""
