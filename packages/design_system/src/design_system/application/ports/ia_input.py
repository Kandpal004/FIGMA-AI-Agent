"""The Phase 11 Information Architecture port — grounds page coverage and navigation tokens.

Supplies neutral :class:`RawSignal` s derived from the IA (page types, navigation depth,
labelling). The infrastructure adapter imports that engine and translates; the design-system
domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["IAInputPort"]


@runtime_checkable
class IAInputPort(Protocol):
    """Gathers information-architecture signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
