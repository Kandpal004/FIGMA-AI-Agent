"""The Specification repository port — persistence for produced specifications.

Specifications are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete implementations;
tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from component_intelligence.domain.report.report import ComponentCompositionSpecification
from component_intelligence.domain.shared.ids import (
    ComponentSpecId,
    ComponentSpecLineageId,
)

__all__ = ["ComponentSpecificationRepository"]


@runtime_checkable
class ComponentSpecificationRepository(Protocol):
    """Persists and loads :class:`ComponentCompositionSpecification` versions."""

    async def save(self, specification: ComponentCompositionSpecification) -> None:
        """Persist a specification version (insert or update by id)."""
        ...

    async def get(
        self, specification_id: ComponentSpecId
    ) -> ComponentCompositionSpecification:
        """Return a specification by id.

        Raises:
            NotFoundError: If no such specification exists.
        """
        ...

    async def latest(
        self, lineage_id: ComponentSpecLineageId
    ) -> ComponentCompositionSpecification:
        """Return the highest-version specification of a lineage.

        Raises:
            NotFoundError: If the lineage has no specifications.
        """
        ...

    async def history(
        self, lineage_id: ComponentSpecLineageId
    ) -> Sequence[ComponentCompositionSpecification]:
        """Return every version of a lineage, oldest first."""
        ...
