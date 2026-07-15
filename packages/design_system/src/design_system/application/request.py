"""The Design System Request — the engine's typed input contract.

A :class:`DesignSystemRequest` carries the *given* context of an engagement — the design-system
brief (the target platforms, the pages in scope, the directions and locales, whether dark mode
is required) and the project. The engine gathers the evidence itself through its input ports;
the caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_system.domain.context.context import DesignSystemBrief, ProjectContext

__all__ = ["DesignSystemRequest"]


@dataclass(frozen=True, slots=True)
class DesignSystemRequest:
    """What the Design System Engine is asked to specify.

    Attributes:
        brief: The design-system brief.
        project: The project context.
    """

    brief: DesignSystemBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
