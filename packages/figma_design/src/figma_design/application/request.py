"""The Figma Design Request — the engine's typed input contract.

A :class:`FigmaDesignRequest` carries the *given* context of an engagement — the Figma brief (the
device classes to render, whether dark mode is required) and the project, plus the optional
:class:`SourceRefs` anchoring which upstream artifacts to model from. The engine gathers the
evidence itself through its input ports; the caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from figma_design.domain.context.context import FigmaBrief, ProjectContext, SourceRefs

__all__ = ["FigmaDesignRequest"]


@dataclass(frozen=True, slots=True)
class FigmaDesignRequest:
    """What the Figma Design Engine is asked to model.

    Attributes:
        brief: The Figma brief.
        project: The project context.
        source_refs: The upstream artifacts to model from (reproducibility anchors).
    """

    brief: FigmaBrief
    project: ProjectContext
    source_refs: SourceRefs = field(default_factory=SourceRefs)

    @property
    def project_id(self) -> str:
        return self.project.project_id
