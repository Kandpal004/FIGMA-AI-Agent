"""The IA Request — the engine's typed input contract.

An :class:`IARequest` carries the *given* context of an engagement — the storefront brief
and the project. The engine gathers the evidence itself through its input ports; the caller
supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from ia.domain.context.context import IABrief, ProjectContext

__all__ = ["IARequest"]


@dataclass(frozen=True, slots=True)
class IARequest:
    """What the Information Architecture Engine is asked to define.

    Attributes:
        brief: The storefront brief.
        project: The project context.
    """

    brief: IABrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
