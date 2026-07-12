# ADR-0011: Prompts and knowledge are configuration, not code

**Status:** Accepted · **Date:** 2026-07-13
**Serves principles:** P9 (no business logic in prompts), P10 (prompts are
configuration), P11 (knowledge is configuration).

## Context

In naive LLM systems, prompts accrete control flow ("if the user asked for X,
then do Y, otherwise reject") and domain knowledge (brand rules, CRO heuristics)
as ever-growing string literals compiled into the code. This is unmaintainable:
prompts can't be versioned or A/B-tested without a deploy, business logic hides
where no test can reach it, and knowledge updates require an engineer.

## Decision

Three hard separations:

1. **Control flow lives in the state machine, reasoning lives in agents, and
   neither lives in prompts.** A prompt frames a role and an output schema; it
   never decides the workflow. Gating, routing, and thresholds are code/config.

2. **Prompts are versioned configuration** loaded through a **Prompt Registry**.
   An agent requests `get_prompt(key, version)` — it never inlines prompt text.
   Backed by files initially; DB-backed and per-tenant-overridable later, so
   prompts can be edited, A/B-tested, and rolled back with no code deploy.

3. **Domain knowledge is configuration + retrieval** in a **Knowledge Base**:
   structured rules as config, semantic knowledge in Qdrant, injected via the
   Tool Layer. Updating a heuristic is a data change, not a code change.

## Consequences

- **+** Prompts and knowledge iterate at product speed, independent of releases.
- **+** Business logic is testable because it lives in code, not prose.
- **+** Per-tenant prompt/knowledge overrides become a config scope, not a fork.
- **−** More moving parts (a registry, a KB) than inline strings — accepted; it
  is the difference between a product and a script.

## Enforcement

Code review rejects: prompt strings hardcoded in agent classes; any prompt that
encodes routing/gating/thresholds; any agent that reads knowledge from source
rather than the KB. The Prompt Registry and Knowledge Base land in the
agent-runtime phase; the agent contract already supports them via `AgentContext`.
