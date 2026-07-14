"""In-memory input adapters — scriptable stand-ins for the signal ports.

These implement the seven input ports with pre-supplied :class:`RawSignal` s, so the engine
runs and is tested with no upstream engines wired. They are the honest default for local
running and tests (a stand-in for the real Phase 3/5/6/7/8/9/13 adapters). A null adapter
returns nothing.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_language.application.contracts import RawSignal
from design_language.domain.context.context import ProjectContext

__all__ = [
    "InMemoryBrandInput",
    "InMemoryBusinessStrategyInput",
    "InMemoryCompetitorInsight",
    "InMemoryCreativeDirectorInput",
    "InMemoryKnowledgeAdvisor",
    "InMemoryPsychologyInput",
    "InMemoryResearchInput",
    "NullBrandInput",
    "NullBusinessStrategyInput",
    "NullCompetitorInsight",
    "NullCreativeDirectorInput",
    "NullKnowledgeAdvisor",
    "NullPsychologyInput",
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


class InMemoryBrandInput(_FixedSignals):
    """A :class:`BrandInputPort` returning fixed brand signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals


class InMemoryPsychologyInput(_FixedSignals):
    """A :class:`PsychologyInputPort` returning fixed psychology signals."""

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals


class InMemoryCreativeDirectorInput(_FixedSignals):
    """A :class:`CreativeDirectorInputPort` returning fixed direction signals."""

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


class InMemoryKnowledgeAdvisor:
    """A :class:`KnowledgeAdvisorPort` returning fixed knowledge signals."""

    def __init__(self, signals: Sequence[RawSignal] = ()) -> None:
        self._signals = tuple(signals)

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        return self._signals


class NullBusinessStrategyInput:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullBrandInput:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullPsychologyInput:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullCreativeDirectorInput:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullResearchInput:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullCompetitorInsight:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()


class NullKnowledgeAdvisor:
    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        return ()
