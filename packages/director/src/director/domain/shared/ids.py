"""Strongly-typed domain identifiers.

Every aggregate and entity in the Director Engine is addressed by a *typed*
identifier rather than a bare :class:`uuid.UUID` or :class:`str`. This is a
deliberate Domain-Driven Design choice with concrete payoffs:

* **Type safety at compile time and runtime.** ``ProjectId`` and ``SectionId``
  are distinct types. A function that expects a ``RunId`` cannot be handed a
  ``StepId`` — the type checker rejects it, and even at runtime the two compare
  unequal because they are different classes. Whole categories of "passed the
  wrong id" bugs simply cannot occur.

* **Self-documenting signatures.** ``def approve(step: StepId) -> None`` says far
  more than ``def approve(step: UUID)``.

* **A single validation and construction seam.** All parsing/validation of the
  underlying UUID happens here, once, and raises a domain exception on bad input
  instead of leaking a stdlib ``ValueError`` into application code.

The identifiers are immutable value objects (frozen dataclasses). They are
hashable and therefore usable as dictionary keys and set members, and they
serialize to a plain UUID string via :func:`str`.

This module depends only on the standard library and on the shared-kernel error
base (:mod:`core.errors`); it imports nothing from the application or
infrastructure layers, in keeping with the Clean Architecture dependency rule.

Testing considerations
----------------------
* ``ProjectId.new()`` returns distinct values on successive calls and is a
  ``ProjectId`` instance.
* Two identifiers of *different* concrete types wrapping the *same* UUID are not
  equal (``ProjectId(u) != SectionId(u)``) and, being different types, are safe
  to key separately.
* ``from_string`` round-trips ``str(id)`` back to an equal identifier and raises
  :class:`InvalidIdentifierError` on malformed input, on ``None``, and on a
  non-string argument.
* Instances are immutable: attribute assignment raises
  :class:`dataclasses.FrozenInstanceError`.
* Constructing the abstract base :class:`Identifier` directly raises
  :class:`InvalidIdentifierError`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "DecisionId",
    "Identifier",
    "InvalidIdentifierError",
    "MemoryRecordId",
    "ProjectId",
    "RunId",
    "SectionId",
    "StepId",
]


class InvalidIdentifierError(DesignDirectorError):
    """Raised when a value cannot form a valid domain identifier.

    Extends the platform's shared-kernel :class:`~core.errors.DesignDirectorError`
    so the API layer can translate it uniformly, while still being specific
    enough for the domain and tests to branch on.
    """

    code = "invalid_identifier"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all typed identifiers — a value object wrapping a UUID.

    Not intended to be instantiated directly; construct one of the concrete
    subclasses (:class:`ProjectId`, :class:`SectionId`, …) instead. Direct
    instantiation is rejected so that an untyped identifier can never enter the
    domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        # Guard against constructing the abstract base itself.
        if type(self) is Identifier:
            raise InvalidIdentifierError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. ProjectId) instead.",
                details={"attempted_type": "Identifier"},
            )
        # Enforce the invariant that `value` is genuinely a UUID. This catches
        # accidental construction from a str/int that would otherwise silently
        # produce a broken identifier.
        if not isinstance(self.value, uuid.UUID):
            raise InvalidIdentifierError(
                f"{type(self).__name__} requires a uuid.UUID, got "
                f"{type(self.value).__name__}.",
                details={"identifier_type": type(self).__name__},
            )

    @classmethod
    def new(cls) -> Self:
        """Generate a fresh, random identifier (UUID version 4).

        Returns:
            A new instance of the concrete identifier type this is called on.
        """
        return cls(uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Self:
        """Parse an identifier from its canonical string form.

        Args:
            raw: A UUID string, typically produced by ``str(identifier)``.

        Returns:
            The parsed identifier of the concrete type this is called on.

        Raises:
            InvalidIdentifierError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidIdentifierError(
                f"{cls.__name__}.from_string expects a str, got "
                f"{type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidIdentifierError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ProjectId(Identifier):
    """Identifies a :class:`~director.domain.project.entities.Project` — a
    storefront design engagement for one tenant."""


@dataclass(frozen=True, slots=True)
class SectionId(Identifier):
    """Identifies a design ``Section`` (hero, product page, cart, …). Each
    section has its own independent lifecycle (Principle P6/P7)."""


@dataclass(frozen=True, slots=True)
class RunId(Identifier):
    """Identifies a single ``WorkflowRun`` — one execution of a workflow
    definition for a section."""


@dataclass(frozen=True, slots=True)
class StepId(Identifier):
    """Identifies a single ``WorkflowStep`` within a run — the unit the State
    Engine tracks and the unit an approval or rejection acts upon."""


@dataclass(frozen=True, slots=True)
class DecisionId(Identifier):
    """Identifies a ``DecisionRecord`` — one append-only entry in the Director's
    reasoning log (Principle P5: every decision is auditable)."""


@dataclass(frozen=True, slots=True)
class MemoryRecordId(Identifier):
    """Identifies a ``MemoryRecord`` in the Memory Engine (Principle P8/P11)."""
