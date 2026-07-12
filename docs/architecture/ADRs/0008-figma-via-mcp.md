# ADR-0008: Figma via MCP, behind the Tool Layer

**Status:** Accepted · **Date:** 2026-07-13

## Context

Agents must read from and write to Figma. Figma exposes a Model Context Protocol
(MCP) surface. If agents spoke MCP directly, the protocol would leak into twenty
agents, tests would require a live MCP server, and swapping the integration would
be a fleet-wide change.

## Decision

Access Figma through a dedicated **MCP client** that lives in the **Tool Layer**.
Agents receive tool adapters via their `AgentContext.tools` and call a stable,
domain-shaped interface — never MCP primitives directly. The same applies to the
Shopify and Magento adapters.

## Consequences

- **+** MCP is an implementation detail behind one seam; agents stay protocol-
  agnostic and mockable.
- **+** Tests inject a fake tool adapter — no live Figma/MCP needed.
- **+** Swapping or upgrading the MCP integration touches one package.
- **−** An extra abstraction layer between agent and Figma — accepted; the
  decoupling and testability are worth it.

## Alternatives considered

- **Agents call MCP directly.** Rejected — protocol leakage and untestability.
- **A single mega-tool object.** Rejected — named, typed adapters per capability
  keep responsibilities clear and independently swappable.

> Phase 1 scope: the Tool Layer is a defined seam (`AgentContext.tools`). The
> concrete Figma MCP client is built in the integration phase.
