"""The UX Request — the engine's typed input contract.

A :class:`UXRequest` carries the *given* context of an engagement — the experience brief
and the project. The engine gathers the evidence itself through its input ports; the
caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from ux.domain.context.context import ProjectContext, UXBrief

__all__ = ["UXRequest"]


@dataclass(frozen=True, slots=True)
class UXRequest:
    """What the UX Strategy Engine is asked to define.

    Attributes:
        brief: The experience brief.
        project: The project context.
    """

    brief: UXBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
