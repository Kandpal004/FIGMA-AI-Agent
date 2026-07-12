# ADR-0001: Monorepo with `packages/` + `apps/`

**Status:** Accepted · **Date:** 2026-07-13

## Context

The product is one system with many parts: a Python backend, a fleet of agents,
an orchestration core, a React console, and shared contracts. These parts change
together — a tweak to the agent contract touches core, orchestration, and the
API in the same logical change.

## Decision

Use a **single monorepo** with a `uv` workspace:

```
packages/   reusable libraries (core, orchestration)
apps/       deployable applications (api, web)
```

`core` and `orchestration` are installable workspace packages; `apps` depend on
them via workspace sources, sharing one lockfile.

## Consequences

- **+** Atomic commits across API + agents + contracts; no version-skew between
  a contract and its consumers.
- **+** One lockfile, one `make check`, shared tooling config.
- **+** Adding a package is a directory + `pyproject.toml`; the workspace glob
  picks it up.
- **−** Requires workspace-aware tooling (`uv`) — accepted; it is the declared
  stack and fast.
- **−** A naive full-repo CI is slower as the tree grows — mitigated later with
  path-scoped CI jobs.

## Alternatives considered

- **Polyrepo (one repo per service).** Rejected: version-skew and cross-repo PRs
  for what is one product at this stage.
- **Flat single package.** Rejected: no enforced boundary between the pure core
  and the deployable apps; the import-direction invariant would erode.
