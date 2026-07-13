"""Command objects — the Director's typed input contract.

Every request that reaches the Director is expressed as one of these immutable
commands. They are the application-layer boundary: the interfaces layer maps
external DTOs onto them, and the Director dispatches on their type. Modelling
requests as explicit value objects (rather than loose kwargs) makes the
Director's surface auditable, validatable, and stable as new request kinds are
added.

All commands are frozen dataclasses carrying only plain data; they perform no
I/O and reference no infrastructure.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from director.domain.shared.ids import ProjectId, RunId, SectionId
from director.domain.shared.value_objects import ExecutionMode, PageType, Priority

__all__ = [
    "ApproveStep",
    "CancelRun",
    "ProvideInput",
    "RejectStep",
    "ResumeRun",
    "SubmitPageDesign",
    "SubmitSectionDesign",
]


def _ro(mapping: Mapping[str, object] | None) -> Mapping[str, object]:
    """Return a read-only copy of a mapping (or an empty one)."""
    return MappingProxyType(dict(mapping or {}))


@dataclass(frozen=True, slots=True)
class SubmitSectionDesign:
    """Design one section: create and drive a SECTION workflow run.

    Attributes:
        tenant_id: Owning tenant.
        project_id: The project the section belongs to.
        section_id: The section to design.
        brief: The design brief / requirements.
        priority: Scheduling priority.
        execution_mode: How the run should execute.
    """

    tenant_id: uuid.UUID
    project_id: ProjectId
    section_id: SectionId
    brief: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    priority: Priority = Priority.NORMAL
    execution_mode: ExecutionMode = ExecutionMode.ASYNCHRONOUS

    def __post_init__(self) -> None:
        object.__setattr__(self, "brief", _ro(self.brief))


@dataclass(frozen=True, slots=True)
class SubmitPageDesign:
    """Design a whole page: create and drive a PAGE workflow run.

    The page run's composite steps each spawn a section run for the matching
    section of the project (resolved by step key).

    Attributes:
        tenant_id: Owning tenant.
        project_id: The project.
        page_section_id: The section representing the page itself.
        page_type: Which page to design.
        brief: The design brief / requirements.
        priority: Scheduling priority.
        execution_mode: How the run should execute.
    """

    tenant_id: uuid.UUID
    project_id: ProjectId
    page_section_id: SectionId
    page_type: PageType
    brief: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    priority: Priority = Priority.NORMAL
    execution_mode: ExecutionMode = ExecutionMode.ASYNCHRONOUS

    def __post_init__(self) -> None:
        object.__setattr__(self, "brief", _ro(self.brief))


@dataclass(frozen=True, slots=True)
class ResumeRun:
    """Resume a paused or in-flight run from its persisted state."""

    run_id: RunId


@dataclass(frozen=True, slots=True)
class ApproveStep:
    """Approve a gate step that is awaiting approval, then continue the run.

    Attributes:
        run_id: The run.
        step_key: The gate step to approve.
        approver: Who approved (for the audit trail).
        notes: Optional approval notes.
    """

    run_id: RunId
    step_key: str
    approver: str = ""
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RejectStep:
    """Reject a gate step that is awaiting approval, triggering rollback.

    Attributes:
        run_id: The run.
        step_key: The gate step to reject.
        approver: Who rejected (for the audit trail).
        notes: The changes required (recorded and fed to the redesign).
    """

    run_id: RunId
    step_key: str
    approver: str = ""
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProvideInput:
    """Supply input that unblocks a BLOCKED step, then continue the run.

    Attributes:
        run_id: The run.
        step_key: The blocked step to unblock.
        input: The supplied data, merged into the run's brief.
    """

    run_id: RunId
    step_key: str
    input: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "input", _ro(self.input))


@dataclass(frozen=True, slots=True)
class CancelRun:
    """Cancel a run.

    Attributes:
        run_id: The run to cancel.
        reason: Optional reason for the audit trail.
    """

    run_id: RunId
    reason: str = ""
