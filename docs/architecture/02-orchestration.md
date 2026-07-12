# Orchestration

The orchestration core is the platform's **Design Director**. Three collaborating
components, each with a single job.

## The three components

### `AgentRegistry` — who fills each role

Maps every `AgentRole` to the concrete `BaseAgent` subclass that implements it and
constructs instances on demand with a shared `AgentContext`. The mediator asks for
"the agent that owns role X" and never names a concrete class — so swapping an
implementation, or A/B-testing two Creative Directors, is a registry change.

```python
registry = AgentRegistry(context)

@registry.register
class ResearchAgent(BaseAgent):
    role = AgentRole.RESEARCH
    async def run(self, agent_input): ...
```

### `StateMachine` — what moves are legal

Pure, synchronous, I/O-free. Given a run and an event, it validates the move
against the transition graph, applies it, and appends an immutable audit record —
returning a **new** `RunRecord` (it never mutates its input). Because it does no
I/O, the entire pipeline logic is unit-testable with plain objects.

### `Mediator` — the loop

The **only** component that invokes agents:

```text
while the run is not finished:
    role  = agent that owns the run's current state
    agent = registry.get(role)
    out   = await agent.run(input_built_from_run)
    event = translate(out.status)          # OK→ADVANCE, REJECTED→REJECT, …
    run   = state_machine.apply(run, event)
    store.save(run)                        # persist EVERY transition
```

Everything hard about a 20-agent system — who runs next, how a veto loops back,
how state survives a crash — is expressed as **data** (the transition graph)
walked by this one small loop.

## Persistence is abstracted

The mediator persists through a `RunStore` protocol (`save` / `load`). An
in-memory store ships for tests and proof-of-wiring; a Postgres-backed store
arrives with the API run endpoints. The same mediator drives both unchanged.

Because every transition is persisted, `Mediator.resume(run_id)` picks a run up
exactly where it left off — the crash-recovery and long-pause entry point.

## Guard rails

- **Redesign cap.** If the Creative Director keeps rejecting, the run fails for
  human review after `max_redesigns` full redesigns rather than looping forever.
- **Output role check.** If an agent returns output tagged with a different role
  than the one invoked, the mediator raises rather than silently mis-filing it.
- **Needs-input pause.** An agent that cannot proceed pauses the run instead of
  failing it, so it can be resumed once the missing input arrives.

## Proven, not asserted

`packages/orchestration/tests/test_pipeline_wiring.py` drives full runs with stub
agents and verifies: the happy path reaches `SECTION_COMPLETE`; a Creative-Director
rejection loops back to `UI` and is recorded with its notes; the redesign guard
trips instead of looping; and `NEEDS_INPUT` pauses the run. These pass today.
