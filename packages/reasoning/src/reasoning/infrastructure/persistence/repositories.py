"""SQLAlchemy implementation of the strategy repository.

Persists a strategy as its codec document plus indexed columns, and reconstructs
it (re-validated) on load. Operates on an injected session; no ORM object escapes.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from reasoning.domain.shared.ids import StrategyId
from reasoning.domain.strategy.strategy import DesignStrategy
from reasoning.infrastructure.persistence import codec
from reasoning.infrastructure.persistence.models import StrategyModel

__all__ = ["SqlAlchemyStrategyRepository"]


class SqlAlchemyStrategyRepository:
    """Postgres-backed :class:`StrategyRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, strategy: DesignStrategy) -> None:
        document = codec.to_document(strategy)
        model = await self._session.get(StrategyModel, strategy.id.value)
        if model is None:
            self._session.add(
                StrategyModel(
                    id=strategy.id.value,
                    project_id=strategy.project_id,
                    section_id=strategy.section_id,
                    page_type=strategy.page_type,
                    stance=strategy.stance.value,
                    overall_confidence=strategy.confidence.overall.value,
                    risk_level=strategy.risk_assessment.overall_level.value,
                    is_actionable=strategy.is_actionable,
                    document=document,
                    created_at=strategy.created_at,
                )
            )
        else:
            model.project_id = strategy.project_id
            model.section_id = strategy.section_id
            model.page_type = strategy.page_type
            model.stance = strategy.stance.value
            model.overall_confidence = strategy.confidence.overall.value
            model.risk_level = strategy.risk_assessment.overall_level.value
            model.is_actionable = strategy.is_actionable
            model.document = document
            model.created_at = strategy.created_at

    async def get(self, strategy_id: StrategyId) -> DesignStrategy:
        model = await self._session.get(StrategyModel, strategy_id.value)
        if model is None:
            raise NotFoundError(
                f"Strategy {strategy_id} not found.",
                details={"strategy_id": str(strategy_id)},
            )
        return codec.from_document(model.document)
