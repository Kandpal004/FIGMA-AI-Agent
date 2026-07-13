"""The Context port — loads brand and project-memory facts for reasoning.

Wraps the Phase-2 Memory Engine behind a decoupled interface: it returns the
engine-local :class:`BrandContext` and :class:`ContextFact` value objects, never
Phase-2 types. An infrastructure adapter translates memory records into these.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from reasoning.domain.request.request import BrandContext, ContextFact

__all__ = ["ContextPort"]


@runtime_checkable
class ContextPort(Protocol):
    """Loads the brand and project-memory context a strategy must honour."""

    async def load_brand(
        self, project_id: str, *, tenant_id: object | None = None
    ) -> BrandContext:
        """Return the brand context for a project (empty if none recorded)."""
        ...

    async def load_memory_facts(
        self,
        project_id: str,
        *,
        section_id: str | None = None,
        tenant_id: object | None = None,
    ) -> Sequence[ContextFact]:
        """Return the project-memory facts relevant to a section."""
        ...
