"""Creative Director inputs — the neutral context the engine reviews over.

These value objects capture the *given* context of a review — the project and the subject
under review — in the engine's own vocabulary, independent of any upstream engine's models.
Infrastructure adapters translate the Phase-12 Wireframe, Phase-11 IA, and the strategy
engines into evidence; the domain never imports those engines. The :class:`ReviewSubject`
identifies *what* is being reviewed (a wireframe plan today, a Figma design in a future
phase) so the same engine extends to new subject kinds without change.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.shared.value_objects import SubjectKind

__all__ = ["InvalidContextError", "ProjectContext", "ReviewSubject"]


class InvalidContextError(DesignDirectorError):
    """Raised when review context is constructed with invalid data."""

    code = "invalid_creative_director_context"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a review serves.

    Attributes:
        project_id: The owning project (UUID string).
        platform: The commerce platform (e.g. "shopify_plus", "adobe_commerce").
        market: The market segment (e.g. "premium", "mass").
        country: The primary country/region.
        tenant_id: The viewer's tenant, for Knowledge scope resolution (UUID string).
    """

    project_id: str
    platform: str = ""
    market: str = ""
    country: str = ""
    tenant_id: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id or not self.project_id.strip():
            raise InvalidContextError("ProjectContext.project_id must be non-empty.")


@dataclass(frozen=True, slots=True)
class ReviewSubject:
    """What the Creative Director is reviewing.

    Attributes:
        kind: The kind of artifact under review.
        reference: The artifact's id in its source engine (the audit anchor).
        label: A human-readable label for the subject.
        phase: The pipeline phase the subject belongs to (e.g. "wireframe").
    """

    kind: SubjectKind
    reference: str
    label: str = ""
    phase: str = ""

    def __post_init__(self) -> None:
        if not self.reference or not self.reference.strip():
            raise InvalidContextError("ReviewSubject.reference must be non-empty.")
