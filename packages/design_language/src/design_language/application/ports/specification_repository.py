"""The Specification repository port — persistence for produced specifications.

Specifications are versioned; the repository stores each version and can return the latest by
lineage and the full history. The infrastructure layer supplies concrete implementations;
tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from design_language.domain.report.report import DesignLanguageSpecification
from design_language.domain.shared.ids import (
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
)

__all__ = ["DesignLanguageSpecificationRepository"]


@runtime_checkable
class DesignLanguageSpecificationRepository(Protocol):
    """Persists and loads :class:`DesignLanguageSpecification` versions."""

    async def save(self, specification: DesignLanguageSpecification) -> None:
        """Persist a specification version (insert or update by id)."""
        ...

    async def get(
        self, specification_id: DesignLanguageSpecId
    ) -> DesignLanguageSpecification:
        """Return a specification by id.

        Raises:
            NotFoundError: If no such specification exists.
        """
        ...

    async def latest(
        self, lineage_id: DesignLanguageSpecLineageId
    ) -> DesignLanguageSpecification:
        """Return the highest-version specification of a lineage.

        Raises:
            NotFoundError: If the lineage has no specifications.
        """
        ...

    async def history(
        self, lineage_id: DesignLanguageSpecLineageId
    ) -> Sequence[DesignLanguageSpecification]:
        """Return every version of a lineage, oldest first."""
        ...
