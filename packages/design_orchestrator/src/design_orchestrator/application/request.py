"""The Orchestration Request — the engine's typed input contract.

An :class:`OrchestrationRequest` carries the *given* context of an engagement — the orchestration
brief (the pages and platforms in scope) and the project, plus the optional :class:`SourceRefs`
anchoring which upstream artifacts to plan from. The engine gathers the evidence itself through
its input ports; the caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from design_orchestrator.domain.context.context import (
    OrchestrationBrief,
    ProjectContext,
    SourceRefs,
)

__all__ = ["OrchestrationRequest"]


@dataclass(frozen=True, slots=True)
class OrchestrationRequest:
    """What the Design Orchestrator is asked to plan.

    Attributes:
        brief: The orchestration brief.
        project: The project context.
        source_refs: The upstream artifacts to orchestrate from (reproducibility anchors).
    """

    brief: OrchestrationBrief
    project: ProjectContext
    source_refs: SourceRefs = field(default_factory=SourceRefs)

    @property
    def project_id(self) -> str:
        return self.project.project_id
