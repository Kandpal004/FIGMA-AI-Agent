"""The Review Request — the engine's typed input contract.

A :class:`ReviewRequest` carries the *given* context of a review — the subject under review,
the policy it is judged by, and the project. The engine gathers the evidence itself through
its input ports; the caller supplies only what to review and how strictly.

Pure application: standard library and the domain models.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.domain.context.context import ProjectContext, ReviewSubject
from creative_director.domain.policy.policy import ReviewPolicy

__all__ = ["ReviewRequest"]


@dataclass(frozen=True, slots=True)
class ReviewRequest:
    """What the Creative Director is asked to review.

    Attributes:
        subject: The artifact under review.
        policy: The profile, mode, and threshold it is judged by.
        project: The project context.
    """

    subject: ReviewSubject
    policy: ReviewPolicy
    project: ProjectContext

    @property
    def project_id(self) -> str:
        return self.project.project_id
