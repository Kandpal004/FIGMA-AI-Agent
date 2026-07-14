"""In-memory input adapters — scriptable stand-ins for the evidence ports.

These implement the four input ports with pre-supplied :class:`RawInsight` s, so the
engine runs and is tested with no upstream engines wired. They are the honest default
for local running and tests (a stand-in for the real Phase 3–6 adapters) and
demonstrate the port contracts in the simplest possible form. A null adapter returns
nothing — valid when a source is unavailable.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.application.contracts import RawInsight
from strategy.domain.context.context import ProjectContext

__all__ = [
    "InMemoryCompetitorInsight",
    "InMemoryKnowledgeAdvisor",
    "InMemoryReasoning",
    "InMemoryResearchInput",
    "NullCompetitorInsight",
    "NullKnowledgeAdvisor",
    "NullReasoning",
    "NullResearchInput",
]


class _FixedInsights:
    """Common base returning a fixed set of insights regardless of project."""

    def __init__(self, insights: Sequence[RawInsight] = ()) -> None:
        self._insights = tuple(insights)


class InMemoryResearchInput(_FixedInsights):
    """A :class:`ResearchInputPort` returning fixed research insights."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        return self._insights


class InMemoryCompetitorInsight(_FixedInsights):
    """A :class:`CompetitorInsightPort` returning fixed competitor insights."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        return self._insights


class InMemoryReasoning(_FixedInsights):
    """A :class:`ReasoningPort` returning fixed reasoning insights."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        return self._insights


class InMemoryKnowledgeAdvisor:
    """A :class:`KnowledgeAdvisorPort` returning fixed knowledge insights."""

    def __init__(self, insights: Sequence[RawInsight] = ()) -> None:
        self._insights = tuple(insights)

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawInsight]:
        return self._insights


class NullResearchInput:
    """A research port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        return ()


class NullCompetitorInsight:
    """A competitor port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        return ()


class NullReasoning:
    """A reasoning port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        return ()


class NullKnowledgeAdvisor:
    """A knowledge advisor that contributes nothing."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawInsight]:
        return ()
