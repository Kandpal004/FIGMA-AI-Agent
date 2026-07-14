"""The Psychology Request — the engine's typed input contract.

A :class:`PsychologyRequest` carries the *given* context of an engagement — the offer
brief and the project. The engine gathers the evidence itself through its input ports;
the caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from psychology.domain.context.context import ProjectContext, PsychologyBrief

__all__ = ["PsychologyRequest"]


@dataclass(frozen=True, slots=True)
class PsychologyRequest:
    """What the Customer Psychology Engine is asked to model.

    Attributes:
        brief: The offer brief.
        project: The project context.
    """

    brief: PsychologyBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
