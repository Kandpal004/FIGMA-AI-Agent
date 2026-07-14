"""Strongly-typed identifiers for the Brand Strategy Engine.

Every addressable thing the engine works with — a brand strategy report and its stable
lineage, the cited evidence it rests on, the brand decisions it makes, and the values,
attributes, differentiators, trust signals, and governance rules those decisions
produce — is referenced by a *typed* identifier rather than a bare :class:`uuid.UUID`
or :class:`str`. As across the rest of the platform, this is a deliberate
Domain-Driven Design choice: distinct id types cannot be confused for one another at
type-check time *or* at runtime, all UUID parsing/validation lives in one place, and
signatures document themselves.

This matters especially here because the brand decision graph cross-references
constantly — a :class:`BrandDecisionEdgeId` links two :class:`BrandDecisionId` s, every
decision cites :class:`BrandEvidenceId` s, and every governance and validation rule
traces back to a decision and its evidence. Typing those references makes an accidental
mix a compile error, not a silent graph corruption.

Two ids encode the versioning model (immutable, versioned reports, consistent with
Phases 3–7):

* :class:`BrandReportLineageId` — the stable lineage identity of a report, constant
  across every re-run version.
* :class:`BrandReportId` — the identity of one immutable report version.

This module depends only on the standard library and the shared-kernel error base
(:mod:`core.errors`); it imports nothing from the application or infrastructure layers,
keeping the Clean Architecture dependency rule intact.

Testing considerations
----------------------
* ``BrandReportId.new()`` yields distinct instances; different concrete id types
  wrapping the same UUID are not equal (``BrandDecisionId(u) != BrandValueId(u)``) and
  hash to separate dictionary keys.
* ``from_string`` round-trips ``str(id)`` and raises :class:`InvalidBrandIdError` on
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
    "BrandAttributeId",
    "BrandDecisionEdgeId",
    "BrandDecisionId",
    "BrandDifferentiatorId",
    "BrandEvidenceId",
    "BrandReportId",
    "BrandReportLineageId",
    "BrandValueId",
    "ConsistencyRuleId",
    "GovernanceRuleId",
    "Identifier",
    "InvalidBrandIdError",
    "TrustSignalId",
    "ValidationRuleId",
]


class InvalidBrandIdError(DesignDirectorError):
    """Raised when a value cannot form a valid brand identifier.

    Extends the platform's shared-kernel
    :class:`~core.errors.DesignDirectorError` so the API layer can translate it
    uniformly, while remaining specific enough for the domain and tests to branch on.
    """

    code = "invalid_brand_id"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Identifier:
    """Abstract base for all brand identifiers — a value object over a UUID.

    Not intended to be instantiated directly; construct one of the concrete subclasses
    (:class:`BrandReportId`, :class:`BrandDecisionId`, …). Direct instantiation is
    rejected so an untyped identifier can never enter the domain.

    Attributes:
        value: The underlying UUID. Immutable.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if type(self) is Identifier:
            raise InvalidBrandIdError(
                "Identifier is abstract; instantiate a concrete subclass "
                "(e.g. BrandReportId) instead.",
                details={"attempted_type": "Identifier"},
            )
        if not isinstance(self.value, uuid.UUID):
            raise InvalidBrandIdError(
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
            InvalidBrandIdError: If ``raw`` is not a well-formed UUID string
                (including ``None`` or a non-string argument).
        """
        if not isinstance(raw, str):
            raise InvalidBrandIdError(
                f"{cls.__name__}.from_string expects a str, got {type(raw).__name__}.",
                details={"identifier_type": cls.__name__},
            )
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidBrandIdError(
                f"{raw!r} is not a valid {cls.__name__}.",
                details={"identifier_type": cls.__name__, "value": raw},
            ) from exc

    def __str__(self) -> str:
        """Return the canonical UUID string, suitable for serialization."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class BrandReportLineageId(Identifier):
    """The stable lineage identity of a brand strategy report, constant across every
    re-run version."""


@dataclass(frozen=True, slots=True)
class BrandReportId(Identifier):
    """The identity of one immutable version of a brand strategy report."""


@dataclass(frozen=True, slots=True)
class BrandEvidenceId(Identifier):
    """Identifies one piece of cited, provenance-tracked evidence."""


@dataclass(frozen=True, slots=True)
class BrandValueId(Identifier):
    """Identifies a brand value."""


@dataclass(frozen=True, slots=True)
class BrandAttributeId(Identifier):
    """Identifies a brand attribute."""


@dataclass(frozen=True, slots=True)
class BrandDifferentiatorId(Identifier):
    """Identifies a brand differentiator."""


@dataclass(frozen=True, slots=True)
class TrustSignalId(Identifier):
    """Identifies a brand trust signal."""


@dataclass(frozen=True, slots=True)
class BrandDecisionId(Identifier):
    """Identifies a brand decision (a node in the brand decision graph)."""


@dataclass(frozen=True, slots=True)
class BrandDecisionEdgeId(Identifier):
    """Identifies a typed edge between two brand decisions."""


@dataclass(frozen=True, slots=True)
class ConsistencyRuleId(Identifier):
    """Identifies a brand consistency rule."""


@dataclass(frozen=True, slots=True)
class GovernanceRuleId(Identifier):
    """Identifies a brand governance rule."""


@dataclass(frozen=True, slots=True)
class ValidationRuleId(Identifier):
    """Identifies a brand validation rule."""
