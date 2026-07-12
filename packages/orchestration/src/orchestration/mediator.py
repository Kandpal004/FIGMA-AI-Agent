"""The mediator — the runtime loop of the Design Director.

The mediator is the *only* component that invokes agents. Its loop is small on
purpose::

    while the run is not finished:
        role  = the agent that owns the run's current state
        agent = registry.get(role)
        out   = await agent.run(input_built_from_run)
        event = translate(out.status)          # OK→ADVANCE, REJECTED→REJECT, ...
        run   = state_machine.apply(run, event)
        store.save(run)

Everything hard about a 20-agent system — who runs next, how a Creative-Director
veto loops back, how state survives a crash — is expressed as *data* (the
transition graph) walked by this one loop, not as branching code scattered
across agents.

Persistence is abstracted behind :class:`RunStore` so the same mediator drives
an in-memory test run and a Postgres-backed production run unchanged. The API
layer supplies a database-backed store in later phases; an in-memory store ships
here so the wiring is provable today.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from core.contracts.agent import AgentInput, AgentOutput, AgentRole, AgentStatus
from core.contracts.workflow import (
    RunRecord,
    RunStatus,
    TransitionEvent,
    WorkflowState,
)
from core.errors import NotFoundError, WorkflowError
from core.logging import get_logger
from orchestration.registry import AgentRegistry
from orchestration.state_machine import StateMachine

log = get_logger(__name__)

#: Safety valve: if the Creative Director keeps rejecting, we must not loop
#: forever. After this many full redesigns the run fails for human review.
DEFAULT_MAX_REDESIGNS = 3


class RunStore(Protocol):
    """Persistence boundary for run records.

    Any backend (in-memory, Postgres, Redis) that implements these two
    coroutines can drive the mediator. This is what lets orchestration stay
    infrastructure-free.
    """

    async def save(self, run: RunRecord) -> None: ...

    async def load(self, run_id: UUID) -> RunRecord: ...


class InMemoryRunStore:
    """A dict-backed :class:`RunStore` for tests and local proof-of-wiring."""

    def __init__(self) -> None:
        self._runs: dict[UUID, RunRecord] = {}

    async def save(self, run: RunRecord) -> None:
        self._runs[run.run_id] = run.model_copy(deep=True)

    async def load(self, run_id: UUID) -> RunRecord:
        run = self._runs.get(run_id)
        if run is None:
            raise NotFoundError(f"Run {run_id} not found.", details={"run_id": str(run_id)})
        return run.model_copy(deep=True)


# Translation from an agent's self-assessed status to a workflow event.
_STATUS_TO_EVENT: dict[AgentStatus, TransitionEvent] = {
    AgentStatus.OK: TransitionEvent.ADVANCE,
    AgentStatus.REJECTED: TransitionEvent.REJECT,
    AgentStatus.FAILED: TransitionEvent.FAIL,
}


class Mediator:
    """Drives a run from its current state to a terminal state."""

    def __init__(
        self,
        registry: AgentRegistry,
        store: RunStore,
        *,
        state_machine: StateMachine | None = None,
        max_redesigns: int = DEFAULT_MAX_REDESIGNS,
    ) -> None:
        self._registry = registry
        self._store = store
        self._sm = state_machine or StateMachine()
        self._max_redesigns = max_redesigns

    async def start(self, run: RunRecord) -> RunRecord:
        """Persist a fresh run and drive it to completion (or a pause/failure)."""
        run = run.model_copy(update={"status": RunStatus.RUNNING})
        await self._store.save(run)
        return await self._drive(run)

    async def resume(self, run_id: UUID) -> RunRecord:
        """Reload a persisted run and continue driving it.

        This is the crash-recovery / long-pause entry point: because every
        transition was persisted, a run picks up exactly where it left off.
        """
        run = await self._store.load(run_id)
        if run.is_terminal():
            return run
        return await self._drive(run)

    # ------------------------------------------------------------------ #
    async def _drive(self, run: RunRecord) -> RunRecord:
        """The core loop. Advances until terminal, paused, or guard-tripped."""
        while not run.is_terminal():
            role_name = self._sm.owner_of_current_state(run)

            # Bootstrap/bookkeeping states (e.g. CREATED) have no owning agent —
            # advance through them without invoking anyone.
            if role_name is None:
                run = self._sm.apply(run, TransitionEvent.ADVANCE)
                await self._store.save(run)
                continue

            # Guard rail: too many Creative-Director redesigns → fail for humans.
            if run.redesign_count > self._max_redesigns:
                run = self._sm.apply(
                    run,
                    TransitionEvent.FAIL,
                    notes=[
                        f"Exceeded max redesigns ({self._max_redesigns}); "
                        "escalating for human review."
                    ],
                )
                await self._store.save(run)
                break

            role = self._resolve_role(role_name)
            output = await self._invoke(run, role)

            # An agent that needs input pauses the run rather than failing it.
            if output.status is AgentStatus.NEEDS_INPUT:
                run = run.model_copy(update={"status": RunStatus.PAUSED})
                await self._store.save(run)
                log.info(
                    "run paused awaiting input",
                    extra={"run_id": str(run.run_id), "state": run.state.value,
                           "role": role.value},
                )
                break

            event = _STATUS_TO_EVENT[output.status]
            run = self._merge_artifact(run, output)
            run = self._sm.apply(
                run, event, agent_role=role.value, notes=output.revision_notes
            )
            await self._store.save(run)

        return run

    # ------------------------------------------------------------------ #
    def _resolve_role(self, role_name: str) -> AgentRole:
        try:
            return AgentRole(role_name)
        except ValueError as exc:  # pragma: no cover - graph is trusted
            raise WorkflowError(
                f"Transition graph references unknown role {role_name!r}.",
                details={"role": role_name},
            ) from exc

    async def _invoke(self, run: RunRecord, role: AgentRole) -> AgentOutput:
        """Build the agent's input from the run, run it, and validate the output."""
        agent = self._registry.get(role)
        agent_input = AgentInput(
            run_id=run.run_id,
            tenant_id=run.tenant_id,
            section=run.section,
            state=run.state,
            brief=run.brief,
            artifacts=run.artifacts,
            revision_notes=self._latest_revision_notes(run),
        )
        output = await agent.run(agent_input)

        if output.role is not role:
            raise WorkflowError(
                f"Agent for role {role.value!r} returned output tagged "
                f"{output.role.value!r}.",
                details={"expected": role.value, "actual": output.role.value},
            )
        return output

    @staticmethod
    def _merge_artifact(run: RunRecord, output: AgentOutput) -> RunRecord:
        """Fold an agent's artifact into the run under its role key."""
        if not output.artifact:
            return run
        merged = {**run.artifacts, output.role.value: output.artifact}
        return run.model_copy(update={"artifacts": merged})

    @staticmethod
    def _latest_revision_notes(run: RunRecord) -> list[str]:
        """The revision notes from the most recent rejection, if the run is
        currently in a redesign loop; otherwise empty."""
        for record in reversed(run.history):
            if record.event is TransitionEvent.REJECT and record.to_state is run.state:
                return record.notes
            if record.to_state is run.state:
                break
        return []
