"""The Business Strategy input port — the primary driver of the brand.

Supplies neutral :class:`RawSignal` s derived from the Phase-7 Business Strategy report
(its directive bundle and cited decisions). This is the brand's principal input: the
brand gives identity to the business strategy. The infrastructure adapter imports Phase
7 and translates; the domain and application never do.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from brand.application.contracts import RawSignal
from brand.domain.context.context import ProjectContext

__all__ = ["BusinessStrategyInputPort"]


@runtime_checkable
class BusinessStrategyInputPort(Protocol):
    """Gathers business-strategy decisions as neutral signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        """Return business-strategy signals for a project (may be empty)."""
        ...
