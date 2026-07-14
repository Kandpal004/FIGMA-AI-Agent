"""The Competitor insight port — optional competitive-friction signals from Phase 5.

Supplies neutral :class:`RawSignal` s about the competitive set's positioning and the
friction it creates for the customer's decision. Optional: a null adapter is valid when
no competitor intelligence is available.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from psychology.application.contracts import RawSignal
from psychology.domain.context.context import ProjectContext

__all__ = ["CompetitorInsightPort"]


@runtime_checkable
class CompetitorInsightPort(Protocol):
    """Gathers competitor signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return competitor-derived signals for a project (may be empty)."""
        ...
