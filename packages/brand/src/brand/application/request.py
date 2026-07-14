"""The Brand Request — the engine's typed input contract.

A :class:`BrandRequest` carries the *given* context of an engagement — the brand brief
and the project. The engine gathers the evidence itself through its input ports; the
caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.context.context import BrandBrief, ProjectContext

__all__ = ["BrandRequest"]


@dataclass(frozen=True, slots=True)
class BrandRequest:
    """What the Brand Strategy Engine is asked to produce a brand for.

    Attributes:
        brief: The brand brief.
        project: The project context.
    """

    brief: BrandBrief
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
