"""The Phase 9 Customer Psychology port — grounds state, motion, and trust tokens.

Supplies neutral :class:`RawSignal` s derived from the customer psychology profile (cognitive
load, trust cues, motion sensitivity). The infrastructure adapter imports that engine and
translates; the design-system domain never imports it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext

__all__ = ["PsychologyInputPort"]


@runtime_checkable
class PsychologyInputPort(Protocol):
    """Gathers customer-psychology signals as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return signals for a project (may be empty)."""
        ...
