# ADR-0009: Typed configuration via Pydantic Settings

**Status:** Accepted · **Date:** 2026-07-13

## Context

A platform with a database, cache, vector store, an LLM provider, and several
external integrations has a large configuration surface. Untyped `os.getenv`
scattered across modules fails late, silently, and inconsistently.

## Decision

Centralize all configuration in one `Settings` object built on **Pydantic
Settings**, sourced from environment variables (and a local `.env`). Every knob
is a validated, typed field. Secrets use `SecretStr`. A weak `SECRET_KEY` is
rejected at startup. Access is via a memoized `get_settings()` singleton.

## Consequences

- **+** Misconfiguration fails **loudly at startup**, not mysteriously at request
  time.
- **+** One documented surface (`.env.example` mirrors the fields 1:1).
- **+** Types and validators catch whole classes of mistakes (bad ports, short
  secrets, malformed lists).
- **−** Tests must supply required env vars or construct `Settings(...)`
  directly — a minor, well-understood cost.

## Alternatives considered

- **Raw `os.environ`.** Rejected — untyped, unvalidated, scattered.
- **Dynaconf / custom loader.** Rejected — Pydantic Settings is already in the
  stack (Pydantic v2) and integrates with our model layer.
