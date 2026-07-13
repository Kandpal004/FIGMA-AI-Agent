"""Shared value objects for the Knowledge Engine.

These immutable, self-validating value objects describe *how strongly* a piece of
knowledge is held, *how important* it is, *where* it applies, and *who* can see
it. They carry no identity and are interchangeable when their attributes match.

Everything here is pure domain: only the standard library and the shared-kernel
error base (:mod:`core.errors`). No I/O, no clock, no global mutable state.

Contents
--------
* :class:`Platform`        — the commerce platforms knowledge can be scoped to.
* :class:`ConfidenceLevel` / :class:`Confidence` — how well-established a
  principle is (a score in ``[0,1]`` and its categorical band).
* :class:`Priority`        — how important a principle is when ranking/conflicting.
* :class:`Tag`             — a normalized free-form label.
* :class:`KnowledgeScope`  — global (universal) vs tenant-scoped visibility.

Testing considerations
----------------------
* :class:`Confidence` validates ``[0,1]``, derives the correct band, and orders
  by score.
* :class:`Tag` normalizes case/whitespace and rejects empties.
* :class:`KnowledgeScope`: a global scope is visible to every tenant; a tenant
  scope only to its own tenant.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "Confidence",
    "ConfidenceLevel",
    "InvalidKnowledgeValueError",
    "KnowledgeScope",
    "Platform",
    "Priority",
    "Tag",
]


class InvalidKnowledgeValueError(DesignDirectorError):
    """Raised when a knowledge value object is constructed with invalid data."""

    code = "invalid_knowledge_value"
    http_status = 422


class Platform(str, Enum):
    """A commerce platform a piece of knowledge may be specific to.

    :data:`AGNOSTIC` marks knowledge that applies regardless of platform.
    """

    SHOPIFY_PLUS = "shopify_plus"
    MAGENTO = "magento"
    AGNOSTIC = "agnostic"


class ConfidenceLevel(str, Enum):
    """The categorical band a :class:`Confidence` score falls into.

    Ordered from most to least established. Used for human-readable reporting and
    for coarse filtering; fine-grained ranking uses the numeric score.
    """

    ESTABLISHED = "established"
    STRONG = "strong"
    MODERATE = "moderate"
    EMERGING = "emerging"
    EXPERIMENTAL = "experimental"

    @property
    def representative_score(self) -> float:
        """A representative numeric score for this band."""
        return _LEVEL_SCORES[self]


_LEVEL_SCORES: dict[ConfidenceLevel, float] = {
    ConfidenceLevel.ESTABLISHED: 0.95,
    ConfidenceLevel.STRONG: 0.80,
    ConfidenceLevel.MODERATE: 0.60,
    ConfidenceLevel.EMERGING: 0.35,
    ConfidenceLevel.EXPERIMENTAL: 0.10,
}


@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """How firmly a piece of knowledge is held — a score in ``[0, 1]``.

    Orders by ``score`` (so confidences are directly comparable for ranking), and
    exposes the categorical :attr:`level` derived from calibrated thresholds.

    Attributes:
        score: A value in ``[0, 1]``.
    """

    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise InvalidKnowledgeValueError(
                "Confidence.score must be within [0, 1].", details={"score": self.score}
            )

    @property
    def level(self) -> ConfidenceLevel:
        """The categorical band this score falls into."""
        if self.score >= 0.9:
            return ConfidenceLevel.ESTABLISHED
        if self.score >= 0.75:
            return ConfidenceLevel.STRONG
        if self.score >= 0.5:
            return ConfidenceLevel.MODERATE
        if self.score >= 0.25:
            return ConfidenceLevel.EMERGING
        return ConfidenceLevel.EXPERIMENTAL

    @classmethod
    def of(cls, score: float) -> Self:
        """Construct from an explicit numeric score."""
        return cls(score=score)

    @classmethod
    def from_level(cls, level: ConfidenceLevel) -> Self:
        """Construct from a categorical band, using its representative score."""
        return cls(score=level.representative_score)

    @classmethod
    def default(cls) -> Self:
        """A sensible default for a curated principle (STRONG)."""
        return cls.from_level(ConfidenceLevel.STRONG)


class Priority(IntEnum):
    """How important a principle is — used to rank and to resolve conflicts.

    An :class:`enum.IntEnum` so priorities compare by rank
    (``Priority.CRITICAL > Priority.NORMAL``). Numeric gaps leave room for future
    levels.
    """

    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40

    @classmethod
    def default(cls) -> Priority:
        """The default priority applied when none is specified."""
        return cls.NORMAL


_TAG_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Tag:
    """A normalized free-form label used for filtering and applicability.

    Values are normalized to lower case with internal whitespace collapsed to a
    single hyphen, so ``Tag("Above The Fold")`` and ``Tag("above the fold")``
    compare equal and key the same set/dict entry.

    Attributes:
        value: The normalized label.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = _TAG_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidKnowledgeValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        """Construct a normalized tag."""
        return cls(value=value)


@dataclass(frozen=True, slots=True)
class KnowledgeScope:
    """The visibility scope of a piece of knowledge.

    Realises the approved global-base + tenant-override model: a ``GLOBAL`` scope
    (``tenant_id is None``) is universal and visible to every tenant; a
    tenant-bound scope is visible only to that tenant, overriding/extending the
    global base for it.

    Attributes:
        tenant_id: The owning tenant, or ``None`` for global knowledge.
    """

    tenant_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        if self.tenant_id is not None and not isinstance(self.tenant_id, uuid.UUID):
            raise InvalidKnowledgeValueError(
                "KnowledgeScope.tenant_id must be a uuid.UUID or None.",
            )

    @property
    def is_global(self) -> bool:
        """Whether this is the universal, tenant-agnostic scope."""
        return self.tenant_id is None

    def visible_to(self, tenant_id: uuid.UUID | None) -> bool:
        """Whether this scope is visible to a viewer.

        Global knowledge is visible to everyone (including anonymous/global
        viewers); tenant knowledge is visible only to its own tenant.
        """
        if self.is_global:
            return True
        return self.tenant_id == tenant_id

    @classmethod
    def global_(cls) -> Self:
        """The universal scope."""
        return cls(tenant_id=None)

    @classmethod
    def tenant(cls, tenant_id: uuid.UUID) -> Self:
        """A tenant-specific scope."""
        return cls(tenant_id=tenant_id)
