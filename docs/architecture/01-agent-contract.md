# The Agent Contract

The agent contract is the load-bearing interface of the whole platform. Every
specialist — Research Agent through Memory Agent — is a subclass of `BaseAgent`
that implements exactly one coroutine:

```python
async def run(self, agent_input: AgentInput) -> AgentOutput
```

That is the entire surface an agent exposes. Its smallness is the point.

## Why so minimal

| Property | How the contract delivers it |
|----------|------------------------------|
| **Testable** | No FastAPI, no DB. Build an `AgentInput`, `await agent.run(...)`, assert on the `AgentOutput`. |
| **Swappable** | The orchestrator depends only on this contract, so any agent can be reimplemented without touching orchestration. |
| **Composable** | Agents are pure with respect to coordination — they never call each other; the mediator routes. |

## The data types

### `AgentInput` (frozen)

Everything an agent needs, nothing more. Treated as read-only.

| Field | Purpose |
|-------|---------|
| `run_id`, `tenant_id` | Identity + tenancy scoping for logs and memory writes. |
| `section` | The page section under design (`hero`, `pdp`, `cart`, …). |
| `state` | The workflow state that triggered this agent. |
| `brief` | The design requirements for this section. |
| `artifacts` | Upstream agents' outputs, keyed by producing role. |
| `revision_notes` | On a redesign, the concrete changes a gatekeeper demanded. |

### `AgentOutput` (frozen)

| Field | Purpose |
|-------|---------|
| `role` | Which agent produced this (validated against the invoked role). |
| `status` | The agent's self-assessment: `OK`, `REJECTED`, `NEEDS_INPUT`, `FAILED`. |
| `artifact` | The structured work product. |
| `summary` | One-paragraph human-readable note for the run timeline. |
| `revision_notes` | On `REJECTED`, what must change. |
| `tokens_input/output`, `model` | Cost/latency observability. |

## Status → workflow event

The agent reports a *status*; the mediator translates it into a workflow *event*:

| `AgentStatus` | `TransitionEvent` | Effect |
|---------------|-------------------|--------|
| `OK` | `ADVANCE` | Move to the next state. |
| `REJECTED` | `REJECT` | Loop back for revision (Reviewer / Creative Director). |
| `FAILED` | `FAIL` | Move to the terminal `FAILED` state. |
| `NEEDS_INPUT` | — | Pause the run (`PAUSED`) awaiting input; no transition. |

This indirection is deliberate: agents express *intent about their own work*;
only the state machine knows what that means for the pipeline.

## Dependency injection

Agents receive capabilities — the LLM client and named tool adapters — through
an `AgentContext` supplied at construction, **not** through `AgentInput`. Runtime
data flows through the input; process-level dependencies flow through the
context. The LLM is typed as a `Protocol` (`LLMPort`) so `core.contracts` carries
no provider dependency and tests can pass a fake.

## The rule an implementer must follow

- Never mutate `agent_input`.
- Return an `AgentOutput` whose `role` equals your declared `role`.
- Be idempotent: the same input should yield equivalent output (so retries and
  resumes are safe).
- Report expected problems via `status=FAILED` + `error`; reserve raising for
  truly unexpected failures.

`BaseAgent` provides `_ok()`, `_rejected()`, and `_failed()` helpers so agents
report results consistently.
