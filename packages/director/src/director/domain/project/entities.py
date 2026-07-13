"""The Project domain: projects, sections, and the context the Director reasons over.

A :class:`Project` is a storefront design engagement owned by a tenant. It is
composed of :class:`Section` s — hero, product page, cart, … — each with its own
independent lifecycle (Principles P6/P7). A :class:`ProjectContext` is the
immutable, read-only snapshot of remembered knowledge (assembled by the Memory
Engine from :class:`~director.domain.memory.entities.MemoryRecord` s) that the
Director loads before every decision so that project context is never lost.

The tenant is referenced by raw UUID rather than a typed id: the tenant is an
organisation owned by the Phase-1 platform, not an aggregate this engine manages,
so it is referenced by value at the boundary.

These are pure domain types with no I/O.

Testing considerations
----------------------
* :class:`Project` enforces unique section keys and offers functional
  ``add_section`` / ``get_section`` (raising :class:`SectionNotFoundError`).
* :class:`ProjectContext` filters records by kind and reports emptiness; it is
  immutable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace

from core.errors import DesignDirectorError

from director.domain.memory.entities import MemoryKind, MemoryRecord
from director.domain.shared.ids import ProjectId, SectionId
from director.domain.shared.value_objects import PageType

__all__ = [
    "DuplicateSectionError",
    "Project",
    "ProjectContext",
    "Section",
    "SectionNotFoundError",
]


class SectionNotFoundError(DesignDirectorError):
    """Raised when a section is requested by a key not present in the project."""

    code = "section_not_found"
    http_status = 404


class DuplicateSectionError(DesignDirectorError):
    """Raised when adding a section whose key already exists in the project."""

    code = "duplicate_section"
    http_status = 409


@dataclass(frozen=True, slots=True)
class Section:
    """A single design section within a project — an independent unit of work.

    Attributes:
        id: Section identity.
        key: Stable slug within the project (e.g. ``"hero"``).
        page_type: The page this section belongs to.
        title: Human-readable label.
    """

    id: SectionId
    key: str
    page_type: PageType
    title: str = ""

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise DesignDirectorError(
                "Section.key must be non-empty.", code="invalid_section"
            )

    @property
    def label(self) -> str:
        """The human label, falling back to the key."""
        return self.title or self.key


@dataclass(frozen=True, slots=True)
class Project:
    """A storefront design engagement — the aggregate root over its sections.

    Attributes:
        id: Project identity.
        tenant_id: Owning tenant (raw UUID; the tenant is a Phase-1 platform
            organisation, referenced by value).
        name: Human-readable name.
        sections: The project's sections, keyed uniquely.
    """

    id: ProjectId
    tenant_id: uuid.UUID
    name: str
    sections: tuple[Section, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.sections, tuple):
            object.__setattr__(self, "sections", tuple(self.sections))
        if not self.name or not self.name.strip():
            raise DesignDirectorError(
                "Project.name must be non-empty.", code="invalid_project"
            )
        seen: set[str] = set()
        for section in self.sections:
            if section.key in seen:
                raise DuplicateSectionError(
                    "Duplicate section key in project.",
                    details={"project_id": str(self.id), "section": section.key},
                )
            seen.add(section.key)

    def has_section(self, key: str) -> bool:
        """Whether a section with ``key`` exists."""
        return any(section.key == key for section in self.sections)

    def get_section(self, key: str) -> Section:
        """Return the section with ``key``.

        Raises:
            SectionNotFoundError: If no such section exists.
        """
        for section in self.sections:
            if section.key == key:
                return section
        raise SectionNotFoundError(
            f"Section {key!r} not found in project {self.id}.",
            details={"project_id": str(self.id), "section": key},
        )

    def add_section(self, section: Section) -> Project:
        """Return a copy of the project with ``section`` added.

        Raises:
            DuplicateSectionError: If the section key already exists.
        """
        if self.has_section(section.key):
            raise DuplicateSectionError(
                "Cannot add a section with a duplicate key.",
                details={"project_id": str(self.id), "section": section.key},
            )
        return replace(self, sections=(*self.sections, section))

    def section_keys(self) -> tuple[str, ...]:
        """The ordered tuple of section keys."""
        return tuple(section.key for section in self.sections)


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """An immutable snapshot of remembered knowledge for a project (and section).

    Assembled by the Memory Engine and handed to the Director so it can reason
    with full context — business goals, brand, constraints, prior decisions —
    without performing its own I/O. A read model, not an aggregate.

    Attributes:
        project_id: The project this context is for.
        section_id: The section, or ``None`` for project-wide context.
        records: The remembered records in scope.
    """

    project_id: ProjectId
    section_id: SectionId | None
    records: tuple[MemoryRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            object.__setattr__(self, "records", tuple(self.records))

    def __len__(self) -> int:
        return len(self.records)

    @property
    def is_empty(self) -> bool:
        """Whether any knowledge is present."""
        return not self.records

    def of_kind(self, kind: MemoryKind) -> tuple[MemoryRecord, ...]:
        """All records of a given kind, in order."""
        return tuple(record for record in self.records if record.kind is kind)

    def first_of(self, kind: MemoryKind) -> MemoryRecord | None:
        """The first record of a given kind, or ``None``."""
        for record in self.records:
            if record.kind is kind:
                return record
        return None
