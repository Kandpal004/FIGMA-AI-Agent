# Architecture Decision Records

Each ADR captures one significant decision: its context, the choice, and its
consequences. They are immutable once accepted — a reversal is a *new* ADR that
supersedes an old one, so the reasoning trail is never lost.

> Every ADR is subordinate to and must cite [the Engineering Principles
> constitution](../PRINCIPLES.md). An ADR may record *how* a principle is met; it
> may never contradict one.

| ADR | Decision | Serves | Status |
|-----|----------|--------|--------|
| [0001](0001-monorepo-layout.md) | Monorepo with `packages/` + `apps/` | — | Accepted |
| [0002](0002-agent-contract.md) | Single `run(AgentInput)->AgentOutput` contract | P1, P2 | Accepted |
| [0003](0003-mediator-orchestration.md) | Mediator orchestration; agents never call agents | P1, P12 | Accepted |
| [0004](0004-custom-state-machine.md) | Custom persisted state machine (not LangGraph/Temporal) | P3, P5 | Accepted |
| [0005](0005-async-execution.md) | Redis + ARQ workers for long agent runs | P3 | Accepted |
| [0006](0006-creative-director-gate.md) | Creative Director as a first-class veto gate | P5, P7 | Accepted |
| [0007](0007-multi-tenancy.md) | `tenant_id` on every row from day one | P4 | Accepted |
| [0008](0008-figma-via-mcp.md) | Figma via MCP behind the Tool Layer | P13 | Accepted |
| [0009](0009-config-pydantic.md) | Typed config via Pydantic Settings | P10 | Accepted |
| [0010](0010-llm-client-abstraction.md) | Single LLM client abstraction | P1 | Accepted |
| [0011](0011-prompts-knowledge-as-config.md) | Prompts & knowledge are configuration, not code | P9, P10, P11 | Accepted |
| [0012](0012-output-renderer-abstraction.md) | Output Renderer abstraction (Figma/HTML/React/Shopify/Magento) | P14, P13 | Accepted |
| [0013](0013-section-lifecycle.md) | Section-level lifecycle + section dossier | P6, P7, P8 | Accepted |
| [0014](0014-agents-service-ready.md) | Agents service-ready; modular monolith, extract on demand | P12 | Accepted |
