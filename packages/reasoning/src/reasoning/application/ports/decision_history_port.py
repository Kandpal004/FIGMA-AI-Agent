"""The Decision-History port — loads prior decisions that constrain reasoning.

Wraps the Phase-2 decision log behind a decoupled interface, returning
:class:`PriorDecisionRef` value objects. Approved prior decisions become premises
in the reason graph, so a new strategy stays consistent with what has already been
decided and approved.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from reasoning.domain.request.request import PriorDecisionRef

__all__ = ["DecisionHistoryPort"]


@runtime_checkable
class DecisionHistoryPort(Protocol):
    """Loads prior decisions relevant to a project/section."""

    async def load_prior_decisions(
        self,
        project_id: str,
        *,
        section_id: str | None = None,
        tenant_id: object | None = None,
    ) -> Sequence[PriorDecisionRef]:
        """Return prior decisions relevant to this reasoning, newest first."""
        ...
