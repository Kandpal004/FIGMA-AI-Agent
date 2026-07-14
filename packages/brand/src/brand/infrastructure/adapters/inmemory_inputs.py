"""In-memory input adapters — scriptable stand-ins for the signal ports.

These implement the five input ports with pre-supplied :class:`RawSignal` s, so the
engine runs and is tested with no upstream engines wired. They are the honest default
for local running and tests (a stand-in for the real Phase 3–7 adapters) and demonstrate
the port contracts in the simplest possible form. A null adapter returns nothing — valid
when a source is unavailable.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.application.contracts import RawSignal
from brand.domain.context.context import ProjectContext

__all__ = [
    "InMemoryBusinessStrategyInput",
    "InMemoryCompetitorInsight",
    "InMemoryKnowledgeAdvisor",
    "InMemoryReasoning",
    "InMemoryResearchInput",
    "NullBusinessStrategyInput",
    "NullCompetitorInsight",
    "NullKnowledgeAdvisor",
    "NullReasoning",
    "NullResearchInput",
]


class _FixedSignals:
    """Common base returning a fixed set of signals regardless of project."""

    def __init__(self, signals: Sequence[RawSignal] = ()) -> None:
        self._signals = tuple(signals)


class InMemoryBusinessStrategyInput(_FixedSignals):
    """A :class:`BusinessStrategyInputPort` returning fixed strategy signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals


class InMemoryResearchInput(_FixedSignals):
    """A :class:`ResearchInputPort` returning fixed research signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals


class InMemoryCompetitorInsight(_FixedSignals):
    """A :class:`CompetitorInsightPort` returning fixed competitor signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals


class InMemoryReasoning(_FixedSignals):
    """A :class:`ReasoningPort` returning fixed reasoning signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals


class InMemoryKnowledgeAdvisor:
    """A :class:`KnowledgeAdvisorPort` returning fixed knowledge signals."""

    def __init__(self, signals: Sequence[RawSignal] = ()) -> None:
        self._signals = tuple(signals)

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        return self._signals


class NullBusinessStrategyInput:
    """A business-strategy port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullResearchInput:
    """A research port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullCompetitorInsight:
    """A competitor port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullReasoning:
    """A reasoning port that contributes nothing."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullKnowledgeAdvisor:
    """A knowledge advisor that contributes nothing."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        return ()
