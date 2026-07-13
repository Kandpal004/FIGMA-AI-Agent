"""The Knowledge Advisor port — the engine's only door to the Knowledge Engine.

The Reasoning Engine never imports the Knowledge Engine (Phase 3). It asks this
port for the applicable, cited principles for a dimension, and receives them as
decoupled :class:`AdvisedPrinciple` DTOs. An infrastructure adapter implements the
port by mapping a :class:`ReasoningDimension` to the right knowledge category and
calling the Phase-3 reasoner; a fake implements it for tests.

Because the advisor returns *cited* principles (each pins a knowledge lineage and
version), the reasoning stays deterministic and grounded: a dimension with no
advised principles becomes an explicit knowledge gap, never a fabrication.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = ["AdvisedPrinciple", "KnowledgeAdvisorPort"]


@dataclass(frozen=True, slots=True)
class AdvisedPrinciple:
    """A cited principle returned by the advisor — a decoupled projection of a
    Knowledge entry, carrying everything needed to pin it as evidence.

    Attributes:
        knowledge_id: The entry's stable lineage id (UUID string).
        entry_version_id: The exact version cited (UUID string).
        category: The entry's knowledge category.
        title: The entry's title.
        statement: The entry's crisp principle.
        source_name: The provenance.
        confidence: The entry's confidence score in ``[0, 1]``.
        relevance: Why the entry applies to the queried dimension/context.
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
    """Supplies the applicable, cited principles for a reasoning dimension."""

    async def advise(
        self,
        dimension: ReasoningDimension,
        *,
        page_type: str | None = None,
        component_type: str | None = None,
        platform: str | None = None,
        contexts: Sequence[str] = (),
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[AdvisedPrinciple]:
        """Return the principles applicable to ``dimension`` under the given
        context, ranked most-relevant first. Empty when the corpus is silent."""
        ...
