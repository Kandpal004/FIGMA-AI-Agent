"""Core primitives for the Ecommerce AI Design Director.

This package holds the pieces every other package depends on and that depend on
nothing internal in return: typed configuration, the agent/workflow contracts,
the LLM client abstraction, structured errors, and logging setup.

Import direction across the codebase is strictly one-way:

    apps/* ──► orchestration ──► core

`core` never imports from `orchestration` or `apps`. Keeping this acyclic is
what lets any of the 20 agents be developed, tested, and swapped in isolation.
"""

from core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
