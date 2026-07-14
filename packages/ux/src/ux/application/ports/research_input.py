"""The Research input port — optional research / VoC evidence from Phase 6.

Supplies neutral :class:`RawSignal` s derived from a project's research report. Optional: a
null adapter is valid when no research is available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext

__all__ = ["ResearchInputPort"]


@runtime_checkable
class ResearchInputPort(Protocol):
    """Gathers research evidence as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return research-derived signals for a project (may be empty)."""
        ...
