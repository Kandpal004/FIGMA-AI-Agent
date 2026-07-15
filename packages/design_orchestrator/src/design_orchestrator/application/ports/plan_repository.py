"""The Plan repository port — persistence for produced execution plans.

Plans are versioned; the repository stores each version and can return the latest by lineage and
the full history. The infrastructure layer supplies concrete implementations; tests supply a
fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_orchestrator.domain.report.report import DesignExecutionPlan
from design_orchestrator.domain.shared.ids import (
    DesignExecutionPlanId,
    DesignExecutionPlanLineageId,
)

__all__ = ["ExecutionPlanRepository"]


@runtime_checkable
class ExecutionPlanRepository(Protocol):
    """Persists and loads :class:`DesignExecutionPlan` versions."""

    async def save(self, plan: DesignExecutionPlan) -> None:
        """Persist a plan version (insert or update by id)."""
        ...

    async def get(self, plan_id: DesignExecutionPlanId) -> DesignExecutionPlan:
        """Return a plan by id.

        Raises:
            NotFoundError: If no such plan exists.
        """
        ...

    async def latest(
        self, lineage_id: DesignExecutionPlanLineageId
    ) -> DesignExecutionPlan:
        """Return the highest-version plan of a lineage.

        Raises:
            NotFoundError: If the lineage has no plans.
        """
        ...

    async def history(
        self, lineage_id: DesignExecutionPlanLineageId
    ) -> Sequence[DesignExecutionPlan]:
        """Return every version of a lineage, oldest first."""
        ...
