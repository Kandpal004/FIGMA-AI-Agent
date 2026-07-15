"""The Specification repository port — persistence for produced specifications.

Specifications are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete implementations; tests
supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_system.domain.report.report import DesignSystemSpecification
from design_system.domain.shared.ids import (
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
)

__all__ = ["DesignSystemSpecificationRepository"]


@runtime_checkable
class DesignSystemSpecificationRepository(Protocol):
    """Persists and loads :class:`DesignSystemSpecification` versions."""

    async def save(self, specification: DesignSystemSpecification) -> None:
        """Persist a specification version (insert or update by id)."""
        ...

    async def get(
        self, specification_id: DesignSystemSpecId
    ) -> DesignSystemSpecification:
        """Return a specification by id.

        Raises:
            NotFoundError: If no such specification exists.
        """
        ...

    async def latest(
        self, lineage_id: DesignSystemSpecLineageId
    ) -> DesignSystemSpecification:
        """Return the highest-version specification of a lineage.

        Raises:
            NotFoundError: If the lineage has no specifications.
        """
        ...

    async def history(
        self, lineage_id: DesignSystemSpecLineageId
    ) -> Sequence[DesignSystemSpecification]:
        """Return every version of a lineage, oldest first."""
        ...
