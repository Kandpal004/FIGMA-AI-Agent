"""Provenance: where a piece of knowledge came from and what backs it up.

Two value objects make the corpus *citable* — a non-negotiable property for a
source of truth:

* :class:`Source` — the origin of an entry (who says so): a research institute, a
  standards body, an internal Creative Director ruling, and so on.
* :class:`Reference` — a specific citation supporting the entry (a book, paper,
  guideline, study, or URL).

Pure domain: standard library plus the shared-kernel error base and the knowledge
identifiers.

Testing considerations
----------------------
* :class:`Source` requires a non-empty name.
* :class:`Reference` requires a non-empty title and rejects an implausible year.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from knowledge.domain.shared.ids import ReferenceId

__all__ = [
    "InvalidProvenanceError",
    "Reference",
    "ReferenceKind",
    "Source",
    "SourceKind",
]


class InvalidProvenanceError(DesignDirectorError):
    """Raised when a source or reference is constructed with invalid data."""

    code = "invalid_provenance"
    http_status = 422


class SourceKind(str, Enum):
    """The kind of origin a piece of knowledge has."""

    RESEARCH_INSTITUTE = "research_institute"
    STANDARDS_BODY = "standards_body"
    ACADEMIC = "academic"
    BOOK = "book"
    INDUSTRY = "industry"
    INTERNAL = "internal"
    CREATIVE_DIRECTOR = "creative_director"
    COMPETITOR = "competitor"
    OTHER = "other"


class ReferenceKind(str, Enum):
    """The kind of a specific citation."""

    BOOK = "book"
    PAPER = "paper"
    ARTICLE = "article"
    GUIDELINE = "guideline"
    STANDARD = "standard"
    STUDY = "study"
    INTERNAL = "internal"
    URL = "url"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Source:
    """The origin of a knowledge entry — who asserts it.

    Attributes:
        name: The originator (e.g. "Nielsen Norman Group", "WCAG 2.2").
        kind: The :class:`SourceKind`.
        url: An optional canonical URL for the source.
        author: An optional specific author.
    """

    name: str
    kind: SourceKind = SourceKind.OTHER
    url: str | None = None
    author: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidProvenanceError("Source.name must be non-empty.")


@dataclass(frozen=True, slots=True)
class Reference:
    """A specific citation backing a knowledge entry.

    Attributes:
        id: Reference identity.
        title: The citation title (required).
        kind: The :class:`ReferenceKind`.
        url: An optional URL.
        author: An optional author.
        year: An optional publication year (validated to a plausible range).
        note: Optional free-text annotation.
    """

    id: ReferenceId
    title: str
    kind: ReferenceKind = ReferenceKind.OTHER
    url: str | None = None
    author: str | None = None
    year: int | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidProvenanceError("Reference.title must be non-empty.")
        if self.year is not None and not (1400 <= self.year <= 2200):
            raise InvalidProvenanceError(
                "Reference.year is implausible.", details={"year": self.year}
            )
