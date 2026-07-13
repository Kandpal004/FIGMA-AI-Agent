"""The Strategy repository port — persistence for produced strategies.

The Reasoning Engine persists each :class:`DesignStrategy` it produces so it can be
retrieved, explained, and (for the Director) gated on before design begins. The
infrastructure layer supplies concrete implementations; tests supply a fake.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from reasoning.domain.strategy.strategy import DesignStrategy
from reasoning.domain.shared.ids import StrategyId

__all__ = ["StrategyRepository"]


@runtime_checkable
class StrategyRepository(Protocol):
    """Persists and loads :class:`DesignStrategy` aggregates."""

    async def save(self, strategy: DesignStrategy) -> None:
        """Persist a produced strategy (insert or update by id)."""
        ...

    async def get(self, strategy_id: StrategyId) -> DesignStrategy:
        """Return a strategy by id.

        Raises:
            NotFoundError: If no such strategy exists.
        """
        ...
