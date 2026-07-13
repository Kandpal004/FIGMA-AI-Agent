"""The Memory domain: what the platform durably remembers, and how it is scoped.

The Memory Engine's job is that the Director "never loses project context". This
module defines the vocabulary of that memory:

* :class:`MemoryKind` — the kinds of knowledge the platform retains (business
  goals, brand tokens, approved/rejected decisions, platform constraints, …),
  taken directly from the product's Memory Engine requirements.
* :class:`MemoryScope` — where a memory applies (a whole project, or one
  section), the value used to scope reads and writes for tenant/project isolation.
* :class:`MemoryRecord` — one immutable unit of remembered knowledge.

These are pure domain types. Persistence (Postgres for structured recall, Qdrant
for semantic recall) is the infrastructure layer's concern; this module knows
nothing of either.

Testing considerations
----------------------
* :class:`MemoryScope` distinguishes project-wide from section-scoped memory and
  :meth:`MemoryScope.covers` returns ``True`` when a broader scope subsumes a
  narrower one.
* :class:`MemoryRecord` validates its ``confidence`` into ``[0, 1]`` and rejects
  an empty ``body``; it is frozen and offers functional updaters.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from types import MappingProxyType

from core.errors import DesignDirectorError

from director.domain.shared.ids import MemoryRecordId, ProjectId, SectionId

__all__ = [
    "InvalidMemoryRecordError",
    "MemoryKind",
    "MemoryRecord",
    "MemoryScope",
]


class InvalidMemoryRecordError(DesignDirectorError):
    """Raised when a memory record is constructed with invalid attributes."""

    code = "invalid_memory_record"
    http_status = 422


class MemoryKind(str, Enum):
    """The kinds of knowledge the Memory Engine retains.

    Mirrors the product's Memory Engine requirements. The value is the stable
    identifier used in persistence and queries.
    """

    BUSINESS_GOAL = "business_goal"
    TARGET_AUDIENCE = "target_audience"
    BRAND_VOICE = "brand_voice"
    BRAND_COLOR = "brand_color"
    TYPOGRAPHY = "typography"
    DESIGN_TOKEN = "design_token"
    APPROVED_DECISION = "approved_decision"
    REJECTED_DECISION = "rejected_decision"
    CREATIVE_DIRECTOR_COMMENT = "creative_director_comment"
    SHOPIFY_CONSTRAINT = "shopify_constraint"
    MAGENTO_CONSTRAINT = "magento_constraint"
    COMPETITOR_REFERENCE = "competitor_reference"
    UX_FINDING = "ux_finding"
    RESEARCH_NOTE = "research_note"


@dataclass(frozen=True, slots=True)
class MemoryScope:
    """Where a memory applies.

    A memory is always bound to a project. A ``section_id`` of ``None`` means the
    memory is project-wide (e.g. brand colours); a set ``section_id`` means it is
    specific to that section (e.g. a UX finding for the hero).

    Attributes:
        project_id: The owning project (always present).
        section_id: The section, or ``None`` for project-wide memory.
    """

    project_id: ProjectId
    section_id: SectionId | None = None

    @property
    def is_project_wide(self) -> bool:
        """Whether this scope applies to the whole project."""
        return self.section_id is None

    def covers(self, other: MemoryScope) -> bool:
        """Whether this scope subsumes ``other``.

        A project-wide scope covers any scope in the same project (project-wide or
        section-specific). A section scope covers only the identical scope.
        """
        if self.project_id != other.project_id:
            return False
        if self.is_project_wide:
            return True
        return self.section_id == other.section_id

    @classmethod
    def project(cls, project_id: ProjectId) -> MemoryScope:
        """A project-wide scope."""
        return cls(project_id=project_id, section_id=None)

    @classmethod
    def section(cls, project_id: ProjectId, section_id: SectionId) -> MemoryScope:
        """A section-specific scope."""
        return cls(project_id=project_id, section_id=section_id)


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """One immutable unit of remembered knowledge.

    Carries both a human/semantic form (``title`` + ``body``, suitable for
    embedding and retrieval) and an optional structured payload (``data``, e.g.
    ``{"hex": "#101820"}`` for a brand colour). Which store persists it — the
    structured store, the semantic store, or both — is decided by the
    infrastructure layer based on ``kind`` and content; the record itself is
    storage-agnostic.

    Attributes:
        id: Record identity.
        scope: Where the memory applies.
        kind: The category of knowledge.
        title: Short label (e.g. "Primary brand colour").
        body: The content, in natural language; embeddable for semantic recall.
        data: Optional structured payload (read-only mapping).
        tags: Free-form tags for filtering.
        source: Where it came from (an agent role, "creative_director", …).
        confidence: A value in ``[0, 1]`` expressing how firmly it is held.
    """

    id: MemoryRecordId
    scope: MemoryScope
    kind: MemoryKind
    title: str
    body: str
    data: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    tags: tuple[str, ...] = ()
    source: str = ""
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.body or not self.body.strip():
            raise InvalidMemoryRecordError(
                "MemoryRecord.body must be non-empty.", details={"id": str(self.id)}
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidMemoryRecordError(
                "MemoryRecord.confidence must be within [0, 1].",
                details={"confidence": self.confidence},
            )
        if not isinstance(self.tags, tuple):
            object.__setattr__(self, "tags", tuple(self.tags))
        # Freeze the structured payload so the record is truly immutable.
        if not isinstance(self.data, MappingProxyType):
            object.__setattr__(self, "data", MappingProxyType(dict(self.data)))

    def with_confidence(self, confidence: float) -> MemoryRecord:
        """Return a copy with a different confidence."""
        return replace(self, confidence=confidence)

    def with_tags(self, tags: tuple[str, ...]) -> MemoryRecord:
        """Return a copy with the given tags."""
        return replace(self, tags=tuple(tags))
