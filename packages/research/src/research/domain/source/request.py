"""The Research Request — the engine's input.

A :class:`ResearchRequest` describes what to research: the project it serves, the
research goal, and the sources to draw from. The engine collects, validates,
normalizes, and structures evidence from these sources into a report.

Pure domain: standard library, the shared-kernel error base, the source entity, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from research.domain.shared.value_objects import Tag
from research.domain.source.source import ResearchSource

__all__ = ["InvalidResearchRequestError", "ResearchRequest"]


class InvalidResearchRequestError(DesignDirectorError):
    """Raised when a research request is constructed with invalid data."""

    code = "invalid_research_request"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """What the Research Engine is asked to acquire.

    Attributes:
        project_id: The project the research serves (UUID string).
        goal: A short statement of what to research.
        sources: The sources to draw from.
        tenant_id: The viewer's tenant, for Knowledge scope resolution.
        tags: Optional tags to attach to the produced results.
    """

    project_id: str
    goal: str
    sources: tuple[ResearchSource, ...] = ()
    tenant_id: object | None = None
    tags: tuple[Tag, ...] = ()

    def __post_init__(self) -> None:
        if not self.project_id or not self.project_id.strip():
            raise InvalidResearchRequestError("ResearchRequest.project_id must be non-empty.")
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "tags", tuple(self.tags))

    def enabled_sources(self) -> tuple[ResearchSource, ...]:
        """The sources that are enabled for collection."""
        return tuple(s for s in self.sources if s.enabled)

    @classmethod
    def build(
        cls,
        project_id: str,
        goal: str,
        *,
        sources: Iterable[ResearchSource] = (),
        tenant_id: object | None = None,
        tags: Iterable[Tag] = (),
    ) -> ResearchRequest:
        return cls(
            project_id=project_id, goal=goal, sources=tuple(sources),
            tenant_id=tenant_id, tags=tuple(tags),
        )
