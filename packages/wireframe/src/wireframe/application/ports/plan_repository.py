"""The Plan repository port — persistence for produced wireframe plans.

Plans are versioned; the repository stores each version and can return the latest by lineage
and the full history. The infrastructure layer supplies concrete implementations; tests
supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from wireframe.domain.report.report import WireframePlan
from wireframe.domain.shared.ids import WireframePlanId, WireframePlanLineageId

__all__ = ["WireframePlanRepository"]


@runtime_checkable
class WireframePlanRepository(Protocol):
    """Persists and loads :class:`WireframePlan` versions."""

    async def save(self, plan: WireframePlan) -> None:
        """Persist a plan version (insert or update by id)."""
        ...

    async def get(self, plan_id: WireframePlanId) -> WireframePlan:
        """Return a plan by id.

        Raises:
            NotFoundError: If no such plan exists.
        """
        ...

    async def latest(self, lineage_id: WireframePlanLineageId) -> WireframePlan:
        """Return the highest-version plan of a lineage.

        Raises:
            NotFoundError: If the lineage has no plans.
        """
        ...

    async def history(self, lineage_id: WireframePlanLineageId) -> Sequence[WireframePlan]:
        """Return every version of a lineage, oldest first."""
        ...
