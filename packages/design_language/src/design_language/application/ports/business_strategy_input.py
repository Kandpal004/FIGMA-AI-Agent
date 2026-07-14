"""The Business-Strategy input port (Phase 7) — grounds business alignment of the language.

Supplies neutral RawSignals derived from its upstream engine. The infrastructure adapter
imports that engine and translates; the design-language domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_language.application.contracts import RawSignal
from design_language.domain.context.context import ProjectContext

__all__ = ["BusinessStrategyInputPort"]


@runtime_checkable
class BusinessStrategyInputPort(Protocol):
    """Gathers signals from its upstream source as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
