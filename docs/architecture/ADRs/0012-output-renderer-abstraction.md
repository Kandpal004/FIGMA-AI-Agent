# ADR-0012: Output Renderer abstraction — Figma is one target of many

**Status:** Accepted · **Date:** 2026-07-13
**Serves principles:** P14 (output-agnostic), P13 (integrations are adapters).

## Context

Figma is where this platform started, but it is only one way to emit a design.
The product must render the same completed design to Figma, HTML, React, a
Shopify theme, and a Magento theme — and add targets later — **without changing
the core.** If the pipeline produced Figma-shaped output directly, every new
target would be a core rewrite and Figma's data model would contaminate every
agent.

## Decision

The pipeline produces a **canonical, target-neutral Design Representation** (a
structured, typed description of a section's layout, tokens, content, and
component tree). Rendering is a separate, pluggable step:

```
Design Representation  ──►  OutputRenderer.render(design) -> Artifact
```

Each target (`figma`, `html`, `react`, `shopify_theme`, `magento_theme`)
implements the `OutputRenderer` port and is **registered**, not hardcoded. Adding
a target = one new renderer package + a registry entry; the core, the agents, and
the state machine do not move. Renderers that call external systems (Figma via
MCP, Shopify Admin API) do so through Tool-Layer adapters (P13).

## Consequences

- **+** New output targets are additive — zero core change (the P14 test).
- **+** The canonical representation is what agents reason about, keeping them
  free of any vendor's model.
- **+** Multiple targets from one design run (Figma *and* React) come for free.
- **−** We must design and maintain the canonical representation carefully — it is
  now a load-bearing contract. Accepted; it is the linchpin of extensibility.

## Alternatives considered

- **Emit Figma directly, adapt later.** Rejected — bakes one vendor's model into
  the core and makes every future target a migration.
- **Per-target agents.** Rejected — duplicates design reasoning per target and
  violates P14; reasoning is target-neutral, rendering is target-specific.

> Scope: this ADR fixes the shape. The canonical Design Representation schema and
> the first renderers are built in the output phase.
