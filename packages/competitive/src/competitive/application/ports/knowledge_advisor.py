"""The Knowledge Advisor port — the engine's grounding in the Knowledge Engine.

Every recommendation, best practice, and adopt/avoid pattern must be backed by a
Knowledge-Engine citation (no opinions). The engine asks this port for the
applicable, cited principles for a dimension, and receives them as decoupled
:class:`AdvisedPrinciple` DTOs. An infrastructure adapter implements it over the
Phase-3 reasoner; a fake implements it for tests. The domain never imports Phase 3.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from competitive.domain.shared.value_objects import CompetitorDimension

__all__ = ["AdvisedPrinciple", "KnowledgeAdvisorPort"]


@dataclass(frozen=True, slots=True)
class AdvisedPrinciple:
    """A cited principle returned by the advisor — everything needed to pin it as
    evidence.

    Attributes:
        knowledge_id: The entry's stable lineage id (UUID string).
        entry_version_id: The exact version cited (UUID string).
        category: The entry's knowledge category.
        title: The entry's title.
        statement: The entry's crisp principle.
        source_name: The provenance.
        confidence: The entry's confidence score in ``[0, 1]``.
        relevance: Why it applies to the queried dimension.
    """

    knowledge_id: str
    entry_version_id: str
    category: str
    title: str
    statement: str
    source_name: str
    confidence: float
    relevance: str = ""


@runtime_checkable
class KnowledgeAdvisorPort(Protocol):
    """Supplies the applicable, cited principles that ground a dimension."""

    async def advise(
        self,
        dimension: CompetitorDimension,
        *,
        industry: str | None = None,
        market: str | None = None,
        contexts: Sequence[str] = (),
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[AdvisedPrinciple]:
        """Return the principles that ground a dimension; empty when silent."""
        ...
