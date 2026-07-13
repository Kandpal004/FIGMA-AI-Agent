"""The Director — the single decision authority of the platform.

The :class:`DirectorService` is the brain. It is the only component permitted to
decide what happens next: it receives every request, loads project context,
selects and creates the workflow run, and then drives that run step by step —
dispatching each agent, interpreting the outcome, applying the correct state
transition, retrying, rolling back, pausing for approval or input, and recording
both its reasoning (decisions) and what happened (events) — until the run reaches
a terminal or paused state. No agent runs except when the Director calls it, and
no step moves except through the State Engine.

It is **framework-independent, pure application logic**. It depends only on the
domain and on ports (interfaces): the Workflow, State, and Memory engines, an
:class:`AgentExecutorPort`, a :class:`UnitOfWorkFactory`, and a :class:`Clock`.
There are no imports of FastAPI, an LLM SDK, MCP, or any database — every
dependency is injected, there is no global state, and there is no singleton.

Durability & resumability
-------------------------
The Director persists the run at every step boundary, atomically with the
decisions that produced it (one Unit of Work per checkpoint). It deliberately
never persists the transient ``RUNNING`` state: a durable checkpoint is always a
``PENDING`` / ``BLOCKED`` / ``WAITING_FOR_APPROVAL`` / terminal state, so a run
interrupted mid-execution resumes cleanly by re-dispatching the step (agents are
idempotent per their contract).

Guard rail
----------
Rollbacks increment the run's redesign counter; once it exceeds ``max_redesigns``
the run fails for human review rather than looping forever.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from core.errors import DesignDirectorError

from director.application.director.commands import (
    ApproveStep,
    CancelRun,
    ProvideInput,
    RejectStep,
    ResumeRun,
    SubmitPageDesign,
    SubmitSectionDesign,
)
from director.application.memory.memory_engine import MemoryEngine
from director.application.ports.agent_executor_port import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentExecutorPort,
    ExecutionStatus,
)
from director.application.ports.clock import Clock
from director.application.ports.unit_of_work import UnitOfWorkFactory
from director.application.state.state_engine import StateEngine
from director.application.workflow.workflow_engine import WorkflowEngine
from director.domain.director.decision import DecisionKind, DecisionRecord
from director.domain.memory.entities import MemoryKind, MemoryScope
from director.domain.project.entities import Project, ProjectContext
from director.domain.shared import events as ev
from director.domain.shared.ids import DecisionId, RunId
from director.domain.state.step_state import StepState
from director.domain.workflow.definition import StepKind, WorkflowDefinition, WorkflowStepSpec
from director.domain.workflow.run import RunStatus, WorkflowRun

__all__ = ["DEFAULT_MAX_REDESIGNS", "DirectorService", "InvalidDirectorOperationError", "RunExecutionResult"]

#: Default cap on full redesigns before a run fails for human review.
DEFAULT_MAX_REDESIGNS = 3


class InvalidDirectorOperationError(DesignDirectorError):
    """Raised when a command is invalid for a run's current state (e.g. approving
    a step that is not awaiting approval)."""

    code = "invalid_director_operation"
    http_status = 409


@dataclass(frozen=True, slots=True)
class RunExecutionResult:
    """The outcome of a Director operation.

    Attributes:
        run: The run in its resulting state.
        events: The domain events emitted during this operation, in order.
    """

    run: WorkflowRun
    events: tuple[ev.DomainEvent, ...]


class DirectorService:
    """Drives workflow runs from request to completion — the platform's brain."""

    def __init__(
        self,
        *,
        workflow_engine: WorkflowEngine,
        state_engine: StateEngine,
        memory_engine: MemoryEngine,
        agent_executor: AgentExecutorPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        max_redesigns: int = DEFAULT_MAX_REDESIGNS,
    ) -> None:
        self._workflow = workflow_engine
        self._state = state_engine
        self._memory = memory_engine
        self._executor = agent_executor
        self._uow = unit_of_work_factory
        self._clock = clock
        self._max_redesigns = max_redesigns

    # ================================================================== #
    # Public API
    # ================================================================== #
    async def submit_section(self, command: SubmitSectionDesign) -> RunExecutionResult:
        """Create and drive a SECTION design run for one section."""
        project = await self._load_project(command.project_id)
        self._assert_tenant(project, command.tenant_id)
        self._assert_section(project, command.section_id)

        definition = self._workflow.section_workflow()
        run = WorkflowRun.from_definition(
            definition,
            run_id=RunId.new(),
            project_id=command.project_id,
            section_id=command.section_id,
            brief=command.brief,
            priority=command.priority,
            execution_mode=command.execution_mode,
        )
        return await self._drive(run, project)

    async def submit_page(self, command: SubmitPageDesign) -> RunExecutionResult:
        """Create and drive a PAGE design run whose composite steps each spawn a
        section run for the matching project section."""
        project = await self._load_project(command.project_id)
        self._assert_tenant(project, command.tenant_id)
        self._assert_section(project, command.page_section_id)

        definition = self._workflow.page_workflow(command.page_type)
        run = WorkflowRun.from_definition(
            definition,
            run_id=RunId.new(),
            project_id=command.project_id,
            section_id=command.page_section_id,
            brief=command.brief,
            priority=command.priority,
            execution_mode=command.execution_mode,
        )
        return await self._drive(run, project)

    async def resume(self, command: ResumeRun) -> RunExecutionResult:
        """Resume a run from its persisted state.

        Progresses runs that are ``RUNNING`` (e.g. interrupted by a crash) or
        ``CREATED``. A run ``PAUSED`` for approval or input is not advanced here —
        it awaits :meth:`approve` / :meth:`reject` / :meth:`provide_input`.
        """
        run, project, _ = await self._load(command.run_id)
        if run.is_terminal or run.status is RunStatus.PAUSED:
            return RunExecutionResult(run, ())
        return await self._drive(run, project)

    async def approve(self, command: ApproveStep) -> RunExecutionResult:
        """Approve a gate step awaiting approval, then continue the run."""
        run, project, definition = await self._load(command.run_id)
        spec = definition.get_step(command.step_key)
        self._require_state(run, command.step_key, StepState.WAITING_FOR_APPROVAL)

        now = self._clock.now()
        events: list[ev.DomainEvent] = []
        run = run.with_status(RunStatus.RUNNING)
        run = self._state.approve(run, command.step_key)
        run = self._state.finalize(run, command.step_key)
        events.append(ev.StepApproved(run_id=run.id, occurred_at=now, step_key=command.step_key))
        await self._remember_manual_decision(run, project, command.step_key, approved=True, notes=command.notes)

        decisions = [
            self._decision(
                run,
                DecisionKind.APPROVE,
                f"Step {command.step_key} approved by {command.approver or 'system'}.",
                now,
                step_key=command.step_key,
            )
        ]
        run, keep_going = await self._advance(run, definition, spec, events, decisions)
        if keep_going:
            return await self._drive(run, project, events)
        return RunExecutionResult(run, tuple(events))

    async def reject(self, command: RejectStep) -> RunExecutionResult:
        """Reject a gate step awaiting approval, triggering rollback, then continue."""
        run, project, definition = await self._load(command.run_id)
        spec = definition.get_step(command.step_key)
        self._require_state(run, command.step_key, StepState.WAITING_FOR_APPROVAL)

        now = self._clock.now()
        events: list[ev.DomainEvent] = []
        run = run.with_status(RunStatus.RUNNING)
        run = self._state.reject(run, command.step_key, command.notes)
        events.append(
            ev.StepRejected(run_id=run.id, occurred_at=now, step_key=command.step_key, notes=tuple(command.notes))
        )
        await self._remember_manual_decision(run, project, command.step_key, approved=False, notes=command.notes)

        decisions = [
            self._decision(
                run,
                DecisionKind.REJECT,
                f"Step {command.step_key} rejected by {command.approver or 'system'}.",
                now,
                step_key=command.step_key,
                data={"notes": list(command.notes)},
            )
        ]
        run, keep_going = await self._rollback(run, definition, spec, command.notes, events, decisions)
        if keep_going:
            return await self._drive(run, project, events)
        return RunExecutionResult(run, tuple(events))

    async def provide_input(self, command: ProvideInput) -> RunExecutionResult:
        """Supply input that unblocks a BLOCKED step, then continue the run."""
        run, project, _ = await self._load(command.run_id)
        self._require_state(run, command.step_key, StepState.BLOCKED)

        now = self._clock.now()
        events: list[ev.DomainEvent] = [ev.RunResumed(run_id=run.id, occurred_at=now)]
        run = run.merge_brief(command.input)
        run = self._state.transition(run, command.step_key, StepState.PENDING)
        run = run.with_status(RunStatus.RUNNING).with_current_step(command.step_key)
        decisions = [
            self._decision(
                run, DecisionKind.RESUME, f"Input provided; unblocking {command.step_key}.", now,
                step_key=command.step_key,
            )
        ]
        await self._persist(run, decisions)
        return await self._drive(run, project, events)

    async def cancel(self, command: CancelRun) -> RunExecutionResult:
        """Cancel a run."""
        run, _project, _ = await self._load(command.run_id)
        if run.is_terminal:
            return RunExecutionResult(run, ())

        now = self._clock.now()
        events: list[ev.DomainEvent] = []
        current = run.current_step_key
        if current is not None:
            step = run.get_step(current)
            if not step.is_terminal:
                run = self._state.cancel(run, current)
        run = run.with_status(RunStatus.CANCELLED)
        events.append(ev.RunCancelled(run_id=run.id, occurred_at=now, reason=command.reason))
        decisions = [
            self._decision(run, DecisionKind.CANCEL, command.reason or "Run cancelled.", now)
        ]
        await self._persist(run, decisions)
        return RunExecutionResult(run, tuple(events))

    # ================================================================== #
    # The loop
    # ================================================================== #
    async def _drive(
        self,
        run: WorkflowRun,
        project: Project,
        events: list[ev.DomainEvent] | None = None,
    ) -> RunExecutionResult:
        """Drive a run until it reaches a terminal or paused state."""
        if events is None:
            events = []
        definition = self._workflow.definition_for_run(run)

        # Start a freshly created run.
        if run.status is RunStatus.CREATED:
            now = self._clock.now()
            first = definition.first_step
            run = run.with_status(RunStatus.RUNNING).with_current_step(first.key)
            events.append(ev.RunStarted(run_id=run.id, occurred_at=now, workflow_key=run.workflow_key))
            await self._persist(
                run,
                [
                    self._decision(
                        run,
                        DecisionKind.SELECT_WORKFLOW,
                        f"Selected workflow {run.workflow_key!r}; starting at {first.key}.",
                        now,
                        step_key=first.key,
                        data={"workflow_version": run.workflow_version},
                    )
                ],
            )

        context = await self._memory.load_context(run.project_id, section_id=run.section_id)

        while run.status is RunStatus.RUNNING and not run.is_terminal:
            step_key = run.current_step_key
            if step_key is None:
                break
            spec = definition.get_step(step_key)
            run, keep_going = await self._process_step(run, project, definition, spec, context, events)
            if not keep_going:
                break

        return RunExecutionResult(run, tuple(events))

    async def _process_step(
        self,
        run: WorkflowRun,
        project: Project,
        definition: WorkflowDefinition,
        spec: WorkflowStepSpec,
        context: ProjectContext,
        events: list[ev.DomainEvent],
    ) -> tuple[WorkflowRun, bool]:
        """Dispatch, execute, and interpret a single step."""
        now = self._clock.now()
        attempt = run.get_step(spec.key).attempt.number
        # Transition to RUNNING in memory only — never persisted (crash-safe).
        run = self._state.start(run, spec.key)
        events.append(
            ev.StepDispatched(
                run_id=run.id,
                occurred_at=now,
                step_key=spec.key,
                agent_role=self._role_value(spec),
                attempt=attempt,
            )
        )
        dispatch = self._decision(
            run, DecisionKind.DISPATCH_STEP,
            f"Dispatching {spec.key} (attempt {attempt}).", now, step_key=spec.key,
            data={"attempt": attempt, "kind": spec.kind.value},
        )

        result = await self._execute_step(run, project, definition, spec, context)

        if result.status is ExecutionStatus.NEEDS_INPUT:
            return await self._block(run, spec, events, [dispatch])
        if result.status is ExecutionStatus.FAILED:
            return await self._retry_or_fail(run, spec, result, events, [dispatch])
        if spec.is_gate:
            return await self._handle_gate(run, definition, spec, result, events, [dispatch])
        if result.status is ExecutionStatus.REJECTED:
            # A non-gate step must not reject; treat as a failure.
            return await self._fail(run, spec, "Non-gate step reported a rejection.", events, [dispatch])

        # Non-gate success: record artifact, complete, advance.
        run = run.with_artifact(spec.key, result.artifact)
        run = self._state.complete(run, spec.key)
        events.append(ev.StepCompleted(run_id=run.id, occurred_at=now, step_key=spec.key))
        advance = self._decision(
            run, DecisionKind.ADVANCE, f"Step {spec.key} completed.", now, step_key=spec.key
        )
        return await self._advance(run, definition, spec, events, [dispatch, advance])

    # ================================================================== #
    # Step execution (agent or composite)
    # ================================================================== #
    async def _execute_step(
        self,
        run: WorkflowRun,
        project: Project,
        definition: WorkflowDefinition,
        spec: WorkflowStepSpec,
        context: ProjectContext,
    ) -> AgentExecutionResult:
        """Run one step: dispatch to its agent, or spawn a sub-workflow."""
        if spec.kind is StepKind.COMPOSITE:
            return await self._spawn_and_drive(run, project, spec)

        assert spec.agent_role is not None  # guaranteed for AGENT steps by the definition
        step = run.get_step(spec.key)
        section_key = next(
            (s.key for s in project.sections if s.id == run.section_id), ""
        )
        request = AgentExecutionRequest(
            run_id=run.id,
            tenant_id=project.tenant_id,
            section_id=run.section_id,
            section=section_key,
            step_key=spec.key,
            agent_role=spec.agent_role,
            attempt=step.attempt.number,
            brief=run.brief,
            artifacts=run.artifacts,
            revision_notes=step.rejection_notes,
            context=context,
        )
        return await self._executor.execute(request)

    async def _spawn_and_drive(
        self, parent_run: WorkflowRun, project: Project, spec: WorkflowStepSpec
    ) -> AgentExecutionResult:
        """Spawn and drive a child run for a composite (page→section) step.

        The composite step's key names the project section the child designs. The
        child is a full, independently-persisted run; its terminal status maps
        back onto this step's outcome.
        """
        assert spec.spawns is not None  # guaranteed for COMPOSITE steps by the definition
        child_def = self._workflow.get_definition(spec.spawns)
        section = project.get_section(spec.key)
        child_run = WorkflowRun.from_definition(
            child_def,
            run_id=RunId.new(),
            project_id=project.id,
            section_id=section.id,
            brief=parent_run.brief,
        )
        child_result = await self._drive(child_run, project)
        child = child_result.run

        status_map = {
            RunStatus.COMPLETED: ExecutionStatus.OK,
            RunStatus.PAUSED: ExecutionStatus.NEEDS_INPUT,
            RunStatus.FAILED: ExecutionStatus.FAILED,
            RunStatus.CANCELLED: ExecutionStatus.FAILED,
        }
        status = status_map.get(child.status, ExecutionStatus.NEEDS_INPUT)
        return AgentExecutionResult(
            status=status,
            summary=f"Section {spec.key!r} run finished as {child.status.value}.",
            artifact={"child_run_id": str(child.id), "child_status": child.status.value},
        )

    # ================================================================== #
    # Outcome handlers (each persists atomically and returns keep_going)
    # ================================================================== #
    async def _advance(
        self,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        spec: WorkflowStepSpec,
        events: list[ev.DomainEvent],
        decisions: list[DecisionRecord],
    ) -> tuple[WorkflowRun, bool]:
        """Move to the next step, or complete the run if this was the last."""
        now = self._clock.now()
        next_spec = self._workflow.next_step(definition, spec.key)
        if next_spec is None:
            run = run.with_current_step(None).with_status(RunStatus.COMPLETED)
            events.append(ev.RunCompleted(run_id=run.id, occurred_at=now))
            decisions = [*decisions, self._decision(run, DecisionKind.COMPLETE, "Run completed.", now)]
            await self._persist(run, decisions)
            return run, False
        run = run.with_current_step(next_spec.key)
        await self._persist(run, decisions)
        return run, True

    async def _handle_gate(
        self,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        spec: WorkflowStepSpec,
        result: AgentExecutionResult,
        events: list[ev.DomainEvent],
        decisions: list[DecisionRecord],
    ) -> tuple[WorkflowRun, bool]:
        """Handle a gate step's outcome: approval (auto or manual) or rejection."""
        now = self._clock.now()

        if result.status is ExecutionStatus.REJECTED:
            run = self._state.await_approval(run, spec.key)
            run = self._state.reject(run, spec.key, result.revision_notes)
            events.append(
                ev.StepRejected(run_id=run.id, occurred_at=now, step_key=spec.key, notes=result.revision_notes)
            )
            decisions = [
                *decisions,
                self._decision(run, DecisionKind.REJECT, f"Gate {spec.key} rejected.", now, step_key=spec.key),
            ]
            return await self._rollback(run, definition, spec, result.revision_notes, events, decisions)

        # Passed: record artifact and move to awaiting-approval.
        run = run.with_artifact(spec.key, result.artifact)
        run = self._state.await_approval(run, spec.key)
        events.append(ev.StepAwaitingApproval(run_id=run.id, occurred_at=now, step_key=spec.key))

        if spec.approval.requires_human:
            run = run.with_status(RunStatus.PAUSED)
            events.append(ev.RunPaused(run_id=run.id, occurred_at=now, reason=f"awaiting approval of {spec.key}"))
            decisions = [
                *decisions,
                self._decision(
                    run, DecisionKind.REQUEST_APPROVAL,
                    f"Awaiting human approval of {spec.key}.", now, step_key=spec.key,
                ),
            ]
            await self._persist(run, decisions)
            return run, False

        # Automatic approval.
        run = self._state.approve(run, spec.key)
        run = self._state.finalize(run, spec.key)
        events.append(ev.StepApproved(run_id=run.id, occurred_at=now, step_key=spec.key))
        decisions = [
            *decisions,
            self._decision(run, DecisionKind.APPROVE, f"Gate {spec.key} auto-approved.", now, step_key=spec.key),
        ]
        return await self._advance(run, definition, spec, events, decisions)

    async def _rollback(
        self,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        gate_spec: WorkflowStepSpec,
        notes: Sequence[str],
        events: list[ev.DomainEvent],
        decisions: list[DecisionRecord],
    ) -> tuple[WorkflowRun, bool]:
        """Rewind a rejected gate to its rollback target for redesign."""
        now = self._clock.now()
        target = self._workflow.resolve_rollback(definition, gate_spec.key)
        if target is None:
            run = run.with_status(RunStatus.FAILED)
            events.append(ev.RunFailed(run_id=run.id, occurred_at=now, reason="rejected without a rollback path"))
            decisions = [*decisions, self._decision(run, DecisionKind.FAIL, "Rejected with no rollback; failing.", now)]
            await self._persist(run, decisions)
            return run, False

        run = run.with_redesign_incremented()
        if run.redesign_count > self._max_redesigns:
            run = run.with_status(RunStatus.FAILED)
            events.append(ev.RunFailed(run_id=run.id, occurred_at=now, reason="exceeded max redesigns"))
            decisions = [
                *decisions,
                self._decision(
                    run, DecisionKind.FAIL,
                    f"Exceeded max redesigns ({self._max_redesigns}); escalating for human review.", now,
                    data={"redesign_count": run.redesign_count},
                ),
            ]
            await self._persist(run, decisions)
            return run, False

        # Reset the redesign span (target … gate) to PENDING for a fresh pass.
        for span_spec in self._workflow.steps_between(definition, target.key, gate_spec.key):
            run = self._state.reset_to_pending(run, span_spec.key)
        # Carry the rejection notes onto the rollback target so its agent sees them.
        run = run.replace_step(run.get_step(target.key).with_rejection_notes(tuple(notes)))
        run = run.with_current_step(target.key)

        events.append(
            ev.StepRolledBack(run_id=run.id, occurred_at=now, from_step=gate_spec.key, to_step=target.key)
        )
        decisions = [
            *decisions,
            self._decision(
                run, DecisionKind.ROLLBACK,
                f"Rolled back from {gate_spec.key} to {target.key} for redesign.", now,
                step_key=target.key, data={"redesign_count": run.redesign_count},
            ),
        ]
        await self._persist(run, decisions)
        return run, True

    async def _retry_or_fail(
        self,
        run: WorkflowRun,
        spec: WorkflowStepSpec,
        result: AgentExecutionResult,
        events: list[ev.DomainEvent],
        decisions: list[DecisionRecord],
    ) -> tuple[WorkflowRun, bool]:
        """Retry a failed step if attempts remain, otherwise fail the run."""
        now = self._clock.now()
        step = run.get_step(spec.key)
        if spec.retry.allows_retry(step.attempt.number):
            run = self._state.retry(run, spec.key)
            new_attempt = run.get_step(spec.key).attempt.number
            events.append(ev.StepRetried(run_id=run.id, occurred_at=now, step_key=spec.key, attempt=new_attempt))
            decisions = [
                *decisions,
                self._decision(
                    run, DecisionKind.RETRY, f"Retrying {spec.key} (attempt {new_attempt}).", now,
                    step_key=spec.key, data={"attempt": new_attempt, "error": result.error},
                ),
            ]
            await self._persist(run, decisions)
            return run, True
        return await self._fail(run, spec, result.error or "step failed", events, decisions)

    async def _block(
        self,
        run: WorkflowRun,
        spec: WorkflowStepSpec,
        events: list[ev.DomainEvent],
        decisions: list[DecisionRecord],
    ) -> tuple[WorkflowRun, bool]:
        """Block a step awaiting external input and pause the run."""
        now = self._clock.now()
        run = self._state.block(run, spec.key)
        run = run.with_status(RunStatus.PAUSED)
        events.append(ev.StepBlocked(run_id=run.id, occurred_at=now, step_key=spec.key))
        events.append(ev.RunPaused(run_id=run.id, occurred_at=now, reason=f"{spec.key} needs input"))
        decisions = [
            *decisions,
            self._decision(run, DecisionKind.BLOCK, f"{spec.key} is blocked awaiting input.", now, step_key=spec.key),
        ]
        await self._persist(run, decisions)
        return run, False

    async def _fail(
        self,
        run: WorkflowRun,
        spec: WorkflowStepSpec,
        reason: str,
        events: list[ev.DomainEvent],
        decisions: list[DecisionRecord],
    ) -> tuple[WorkflowRun, bool]:
        """Fail a step and the run."""
        now = self._clock.now()
        run = self._state.fail(run, spec.key)
        run = run.with_status(RunStatus.FAILED)
        events.append(ev.StepFailed(run_id=run.id, occurred_at=now, step_key=spec.key, error=reason))
        events.append(ev.RunFailed(run_id=run.id, occurred_at=now, reason=reason))
        decisions = [
            *decisions,
            self._decision(run, DecisionKind.FAIL, f"{spec.key} failed: {reason}", now, step_key=spec.key),
        ]
        await self._persist(run, decisions)
        return run, False

    # ================================================================== #
    # Helpers
    # ================================================================== #
    async def _load_project(self, project_id: object) -> Project:
        async with self._uow() as uow:
            return await uow.projects.get(project_id)  # type: ignore[arg-type]

    async def _load(self, run_id: RunId) -> tuple[WorkflowRun, Project, WorkflowDefinition]:
        async with self._uow() as uow:
            run = await uow.runs.get(run_id)
            project = await uow.projects.get(run.project_id)
        definition = self._workflow.definition_for_run(run)
        return run, project, definition

    async def _persist(self, run: WorkflowRun, decisions: Sequence[DecisionRecord]) -> None:
        """Persist the run and its decisions atomically in one transaction."""
        async with self._uow() as uow:
            await uow.runs.save(run)
            for decision in decisions:
                await uow.decisions.append(decision)
            await uow.commit()

    async def _remember_manual_decision(
        self, run: WorkflowRun, project: Project, step_key: str, *, approved: bool, notes: Sequence[str]
    ) -> None:
        """Record a human gate decision in memory (approved/rejected)."""
        scope = MemoryScope.section(project.id, run.section_id)
        kind = MemoryKind.APPROVED_DECISION if approved else MemoryKind.CREATIVE_DIRECTOR_COMMENT
        verb = "approved" if approved else "rejected"
        body = f"Gate {step_key} {verb}." + (f" Notes: {'; '.join(notes)}" if notes else "")
        await self._memory.remember_fact(
            scope, kind, title=f"{step_key} {verb}", body=body,
            data={"step": step_key, "notes": list(notes)}, source="creative_director",
        )

    def _decision(
        self,
        run: WorkflowRun,
        kind: DecisionKind,
        summary: str,
        now: object,
        *,
        step_key: str | None = None,
        data: dict[str, object] | None = None,
    ) -> DecisionRecord:
        return DecisionRecord(
            id=DecisionId.new(),
            run_id=run.id,
            kind=kind,
            summary=summary,
            occurred_at=now,  # type: ignore[arg-type]  # Clock returns datetime
            step_key=step_key,
            data=data or {},
        )

    @staticmethod
    def _role_value(spec: WorkflowStepSpec) -> str | None:
        return spec.agent_role.value if spec.agent_role is not None else None

    @staticmethod
    def _assert_tenant(project: Project, tenant_id: object) -> None:
        if project.tenant_id != tenant_id:
            raise InvalidDirectorOperationError(
                "Tenant does not own this project.",
                details={"project_id": str(project.id)},
            )

    @staticmethod
    def _assert_section(project: Project, section_id: object) -> None:
        if not any(section.id == section_id for section in project.sections):
            raise InvalidDirectorOperationError(
                "Section does not belong to the project.",
                details={"project_id": str(project.id), "section_id": str(section_id)},
            )

    def _require_state(self, run: WorkflowRun, step_key: str, expected: StepState) -> None:
        step = run.get_step(step_key)
        if step.state is not expected:
            raise InvalidDirectorOperationError(
                f"Step {step_key} is {step.state.value}, expected {expected.value}.",
                details={"run_id": str(run.id), "step": step_key, "state": step.state.value},
            )
