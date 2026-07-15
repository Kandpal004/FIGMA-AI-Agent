"""The Model repository port — persistence for produced Figma design models.

Models are versioned; the repository stores each version and can return the latest by lineage and
the full history. The infrastructure layer supplies concrete implementations; tests supply a fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.shared.ids import (
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
)

__all__ = ["FigmaModelRepository"]


@runtime_checkable
class FigmaModelRepository(Protocol):
    """Persists and loads :class:`FigmaDesignModel` versions."""

    async def save(self, model: FigmaDesignModel) -> None:
        """Persist a model version (insert or update by id)."""
        ...

    async def get(self, model_id: FigmaDesignModelId) -> FigmaDesignModel:
        """Return a model by id.

        Raises:
            NotFoundError: If no such model exists.
        """
        ...

    async def latest(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> FigmaDesignModel:
        """Return the highest-version model of a lineage.

        Raises:
            NotFoundError: If the lineage has no models.
        """
        ...

    async def history(
        self, lineage_id: FigmaDesignModelLineageId
    ) -> Sequence[FigmaDesignModel]:
        """Return every version of a lineage, oldest first."""
        ...
