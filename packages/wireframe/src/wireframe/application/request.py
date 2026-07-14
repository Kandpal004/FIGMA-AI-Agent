"""The Wireframe Request — the engine's typed input contract.

A :class:`WireframeRequest` carries the *given* context of an engagement — the storefront
brief and the project. The engine gathers the evidence itself through its input ports; the
caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from wireframe.domain.context.context import ProjectContext, WireframeBrief

__all__ = ["WireframeRequest"]


@dataclass(frozen=True, slots=True)
class WireframeRequest:
    """What the Wireframe Planning Engine is asked to plan.

    Attributes:
        brief: The storefront brief.
        project: The project context.
    """

    brief: WireframeBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
