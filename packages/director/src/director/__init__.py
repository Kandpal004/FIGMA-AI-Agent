"""Ecommerce AI Design Director — the AI Director Engine (Phase 2).

The brain of the platform: a framework-independent, Clean-Architecture engine
that controls every agent, workflow, approval, retry, rollback, memory and
project state. The Director is the only component permitted to decide what
happens next.

Layers (dependencies point inward only):

* ``domain``         — pure entities, value objects, the step-state machine, and
  workflow definitions. No I/O, no frameworks.
* ``application``    — the Director, Workflow, State and Memory engines, plus the
  ports (interfaces) the infrastructure implements.
* ``infrastructure`` — adapters: the Phase-1 agent-executor bridge, in-memory and
  SQLAlchemy persistence, the Postgres memory store, and the composition roots.
* ``interfaces``     — the inbound facade and the serializable view DTOs.

Entry points: :func:`director.infrastructure.container.build_in_memory_environment`
for local/testing, and
:func:`director.infrastructure.persistence.wiring.build_sqlalchemy_environment`
for a database-backed deployment.
"""

__all__: list[str] = []
