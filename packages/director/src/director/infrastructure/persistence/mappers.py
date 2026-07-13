"""Mappers between ORM rows and domain aggregates.

Keeping the mapping in one place is what lets the domain stay free of SQLAlchemy:
domain objects never inherit from ``Base`` or carry ORM state. Each function is a
pure translation in one direction; the repositories call them at the boundary.
"""

from __future__ import annotations

from director.domain.director.decision import DecisionKind, DecisionRecord
from director.domain.memory.entities import MemoryKind, MemoryRecord, MemoryScope
from director.domain.project.entities import Project, Section
from director.domain.shared.ids import (
    DecisionId,
    MemoryRecordId,
    ProjectId,
    RunId,
    SectionId,
    StepId,
)
from director.domain.shared.value_objects import (
    Attempt,
    ExecutionMode,
    PageType,
    Priority,
    WorkflowType,
)
from director.domain.state.step_state import StepState
from director.domain.workflow.run import RunStatus, WorkflowRun, WorkflowStep
from director.infrastructure.persistence.models import (
    DecisionModel,
    MemoryRecordModel,
    ProjectModel,
    RunModel,
)

__all__ = [
    "decision_to_model",
    "memory_to_model",
    "model_to_decision",
    "model_to_memory",
    "model_to_project",
    "model_to_run",
    "project_to_model",
    "run_to_model",
]


# --------------------------------------------------------------------------- #
# Project
# --------------------------------------------------------------------------- #
def _section_to_dict(section: Section) -> dict:
    return {
        "id": str(section.id),
        "key": section.key,
        "page_type": section.page_type.value,
        "title": section.title,
    }


def _dict_to_section(raw: dict) -> Section:
    return Section(
        id=SectionId.from_string(raw["id"]),
        key=raw["key"],
        page_type=PageType(raw["page_type"]),
        title=raw.get("title", ""),
    )


def project_to_model(project: Project) -> ProjectModel:
    return ProjectModel(
        id=project.id.value,
        tenant_id=project.tenant_id,
        name=project.name,
        sections=[_section_to_dict(s) for s in project.sections],
    )


def apply_project(model: ProjectModel, project: Project) -> None:
    """Update an existing ORM row in place from a domain project."""
    model.tenant_id = project.tenant_id
    model.name = project.name
    model.sections = [_section_to_dict(s) for s in project.sections]


def model_to_project(model: ProjectModel) -> Project:
    return Project(
        id=ProjectId(model.id),
        tenant_id=model.tenant_id,
        name=model.name,
        sections=tuple(_dict_to_section(s) for s in model.sections),
    )


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def _step_to_dict(step: WorkflowStep) -> dict:
    return {
        "id": str(step.id),
        "key": step.key,
        "state": step.state.value,
        "attempt_number": step.attempt.number,
        "attempt_limit": step.attempt.limit,
        "rejection_notes": list(step.rejection_notes),
        "output_summary": step.output_summary,
    }


def _dict_to_step(raw: dict) -> WorkflowStep:
    return WorkflowStep(
        id=StepId.from_string(raw["id"]),
        key=raw["key"],
        attempt=Attempt(number=raw["attempt_number"], limit=raw["attempt_limit"]),
        state=StepState(raw["state"]),
        rejection_notes=tuple(raw.get("rejection_notes", ())),
        output_summary=raw.get("output_summary", ""),
    )


def run_to_model(run: WorkflowRun) -> RunModel:
    return RunModel(
        id=run.id.value,
        project_id=run.project_id.value,
        section_id=run.section_id.value,
        workflow_key=run.workflow_key,
        workflow_version=run.workflow_version,
        workflow_type=run.workflow_type.value,
        status=run.status.value,
        current_step_key=run.current_step_key,
        priority=int(run.priority),
        execution_mode=run.execution_mode.value,
        redesign_count=run.redesign_count,
        steps=[_step_to_dict(s) for s in run.steps],
        brief=dict(run.brief),
        artifacts=dict(run.artifacts),
    )


def apply_run(model: RunModel, run: WorkflowRun) -> None:
    """Update an existing ORM row in place from a domain run."""
    model.workflow_key = run.workflow_key
    model.workflow_version = run.workflow_version
    model.workflow_type = run.workflow_type.value
    model.status = run.status.value
    model.current_step_key = run.current_step_key
    model.priority = int(run.priority)
    model.execution_mode = run.execution_mode.value
    model.redesign_count = run.redesign_count
    model.steps = [_step_to_dict(s) for s in run.steps]
    model.brief = dict(run.brief)
    model.artifacts = dict(run.artifacts)


def model_to_run(model: RunModel) -> WorkflowRun:
    return WorkflowRun(
        id=RunId(model.id),
        project_id=ProjectId(model.project_id),
        section_id=SectionId(model.section_id),
        workflow_key=model.workflow_key,
        workflow_version=model.workflow_version,
        workflow_type=WorkflowType(model.workflow_type),
        steps=tuple(_dict_to_step(s) for s in model.steps),
        status=RunStatus(model.status),
        current_step_key=model.current_step_key,
        priority=Priority(model.priority),
        execution_mode=ExecutionMode(model.execution_mode),
        brief=dict(model.brief),
        artifacts=dict(model.artifacts),
        redesign_count=model.redesign_count,
    )


# --------------------------------------------------------------------------- #
# Decision
# --------------------------------------------------------------------------- #
def decision_to_model(decision: DecisionRecord) -> DecisionModel:
    return DecisionModel(
        id=decision.id.value,
        run_id=decision.run_id.value,
        kind=decision.kind.value,
        summary=decision.summary,
        step_key=decision.step_key,
        data=dict(decision.data),
        occurred_at=decision.occurred_at,
    )


def model_to_decision(model: DecisionModel) -> DecisionRecord:
    return DecisionRecord(
        id=DecisionId(model.id),
        run_id=RunId(model.run_id),
        kind=DecisionKind(model.kind),
        summary=model.summary,
        occurred_at=model.occurred_at,
        step_key=model.step_key,
        data=dict(model.data),
    )


# --------------------------------------------------------------------------- #
# Memory
# --------------------------------------------------------------------------- #
def memory_to_model(record: MemoryRecord) -> MemoryRecordModel:
    return MemoryRecordModel(
        id=record.id.value,
        project_id=record.scope.project_id.value,
        section_id=record.scope.section_id.value if record.scope.section_id else None,
        kind=record.kind.value,
        title=record.title,
        body=record.body,
        data=dict(record.data),
        tags=list(record.tags),
        source=record.source,
        confidence=record.confidence,
    )


def model_to_memory(model: MemoryRecordModel) -> MemoryRecord:
    scope = MemoryScope(
        project_id=ProjectId(model.project_id),
        section_id=SectionId(model.section_id) if model.section_id else None,
    )
    return MemoryRecord(
        id=MemoryRecordId(model.id),
        scope=scope,
        kind=MemoryKind(model.kind),
        title=model.title,
        body=model.body,
        data=dict(model.data),
        tags=tuple(model.tags),
        source=model.source,
        confidence=model.confidence,
    )
