# ADR-0010: A single LLM client abstraction

**Status:** Accepted · **Date:** 2026-07-13

## Context

Every reasoning agent calls a language model. Cross-cutting concerns — retries,
timeouts, backoff, token accounting, and model routing (Opus for deep reasoning,
Haiku for mechanical work) — must not be re-implemented in each of twenty agents.

## Decision

Provide one `LLMClient` (Anthropic Claude) behind a narrow `LLMPort` protocol.
Agents receive it via `AgentContext.llm` and call `complete(...)`. The client
owns:

- **Model routing** via symbolic tiers (`"default"` / `"fast"`) resolved from
  settings, so the whole fleet retunes centrally.
- **Retries with exponential backoff** on transient errors, bounded by config.
- **Uniform error mapping** onto `core.errors`.
- **Token accounting** returned on every response.

The Anthropic SDK is imported lazily so `core` (and contract-only tests) load
without it.

## Consequences

- **+** One place to tune reliability, cost, and model policy for all agents.
- **+** Agents depend on a `Protocol`, not a vendor SDK — easy to fake in tests.
- **+** Per-agent model selection without per-agent plumbing.
- **−** A thin indirection over the SDK — negligible, and it earns its keep at
  the first cross-cutting change (rate-limit handling, a model swap, cost caps).

## Alternatives considered

- **Direct SDK calls in agents.** Rejected — duplicated reliability logic and
  vendor lock-in spread across twenty files.
- **A multi-provider gateway (LiteLLM etc.).** Deferred — Claude is the chosen
  primary; the `LLMPort` seam leaves room to add one later without touching
  agents.
