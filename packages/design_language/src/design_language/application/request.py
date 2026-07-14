"""The Design Language Request — the engine's typed input contract.

A :class:`DesignLanguageRequest` carries the *given* context of an engagement — the design
brief (industry, tier, optional archetype hint) and the project. The engine gathers the
evidence itself through its input ports; the caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_language.domain.context.context import DesignBrief, ProjectContext

__all__ = ["DesignLanguageRequest"]


@dataclass(frozen=True, slots=True)
class DesignLanguageRequest:
    """What the Design Language Engine is asked to define.

    Attributes:
        brief: The design brief.
        project: The project context.
    """

    brief: DesignBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
