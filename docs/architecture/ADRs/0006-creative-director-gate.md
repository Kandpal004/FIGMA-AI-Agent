# ADR-0006: Creative Director as a first-class veto gate

**Status:** Accepted · **Date:** 2026-07-13

## Context

The product mandates that the Creative Director holds **final authority**: if it
rejects a design, everything goes back for redesign. Encoding this as an ad-hoc
`if cd_rejected: ...` somewhere would make the single most important business
rule invisible and unauditable.

## Decision

Model the Creative Director as a dedicated workflow state,
`CREATIVE_DIRECTOR_GATE`, with two outgoing transitions:

- `ADVANCE` (approve) → `SECTION_COMPLETE` — the *only* path to shipping.
- `REJECT` (veto) → `UI` — loops the whole section back for redesign and
  increments `redesign_count`.

A guard rail caps redesigns; beyond it the run fails for human review rather than
looping forever.

## Consequences

- **+** The business rule is explicit, visible in the graph, and enforced by the
  state machine — a section cannot reach `SECTION_COMPLETE` without CD approval.
- **+** Every rejection is persisted with its notes — full accountability.
- **+** The redesign counter enables reporting and the guard rail.
- **−** A strict gate can bottleneck throughput — acceptable and intended; it is
  the product's core quality mechanism.

## Alternatives considered

- **CD as a normal reviewer.** Rejected — understates its final authority and
  its distinct redesign-to-UI loop.
- **Inline conditional in the mediator.** Rejected — hides the rule and defeats
  auditability.
