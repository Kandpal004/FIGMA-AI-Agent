# Architecture Decision Records

Each ADR captures one significant decision: its context, the choice, and its
consequences. They are immutable once accepted — a reversal is a *new* ADR that
supersedes an old one, so the reasoning trail is never lost.

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-monorepo-layout.md) | Monorepo with `packages/` + `apps/` | Accepted |
| [0002](0002-agent-contract.md) | Single `run(AgentInput)->AgentOutput` contract | Accepted |
| [0003](0003-mediator-orchestration.md) | Mediator orchestration; agents never call agents | Accepted |
| [0004](0004-custom-state-machine.md) | Custom persisted state machine (not LangGraph/Temporal) | Accepted |
| [0005](0005-async-execution.md) | Redis + ARQ workers for long agent runs | Accepted |
| [0006](0006-creative-director-gate.md) | Creative Director as a first-class veto gate | Accepted |
| [0007](0007-multi-tenancy.md) | `tenant_id` on every row from day one | Accepted |
| [0008](0008-figma-via-mcp.md) | Figma via MCP behind the Tool Layer | Accepted |
| [0009](0009-config-pydantic.md) | Typed config via Pydantic Settings | Accepted |
| [0010](0010-llm-client-abstraction.md) | Single LLM client abstraction | Accepted |
