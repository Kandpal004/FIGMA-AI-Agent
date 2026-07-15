"""The Component Intelligence Request — the engine's typed input contract.

A :class:`ComponentIntelligenceRequest` carries the *given* context of an engagement — the
composition brief (the pages in scope, typically inherited from the wireframe plan) and the
project. The engine gathers the evidence itself through its input ports; the caller supplies
only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.domain.context.context import CompositionBrief, ProjectContext

__all__ = ["ComponentIntelligenceRequest"]


@dataclass(frozen=True, slots=True)
class ComponentIntelligenceRequest:
    """What the Component Intelligence Engine is asked to compose.

    Attributes:
        brief: The composition brief.
        project: The project context.
    """

    brief: CompositionBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
