"""In-memory input adapters — scriptable stand-ins for the signal ports.

These implement the eleven input ports with pre-supplied :class:`RawSignal` s, so the engine runs
and is tested with no upstream engines wired. They are the honest default for local running and
tests (a stand-in for the real Phase 3–16 adapters). A null adapter returns nothing.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext

__all__ = [
    "InMemoryBrandInput",
    "InMemoryBusinessStrategyInput",
    "InMemoryComponentIntelligenceInput",
    "InMemoryCreativeDirectorInput",
    "InMemoryDesignLanguageInput",
    "InMemoryDesignSystemInput",
    "InMemoryIAInput",
    "InMemoryKnowledgeAdvisor",
    "InMemoryPsychologyInput",
    "InMemoryUXInput",
    "InMemoryWireframeInput",
    "NullBrandInput",
    "NullBusinessStrategyInput",
    "NullComponentIntelligenceInput",
    "NullCreativeDirectorInput",
    "NullDesignLanguageInput",
    "NullDesignSystemInput",
    "NullIAInput",
    "NullKnowledgeAdvisor",
    "NullPsychologyInput",
    "NullUXInput",
    "NullWireframeInput",
]


class _FixedSignals:
    """Common base returning a fixed set of signals regardless of project."""

    def __init__(self, signals: Sequence[RawSignal] = ()) -> None:
        self._signals = tuple(signals)


def _gather_class(name: str) -> type:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return self._signals

    return type(name, (_FixedSignals,), {"gather": gather, "__doc__": f"In-memory {name}."})


def _null_class(name: str) -> type:
    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        return ()

    return type(name, (), {"gather": gather, "__doc__": f"Null {name}."})


InMemoryDesignSystemInput = _gather_class("InMemoryDesignSystemInput")
InMemoryComponentIntelligenceInput = _gather_class("InMemoryComponentIntelligenceInput")
InMemoryWireframeInput = _gather_class("InMemoryWireframeInput")
InMemoryCreativeDirectorInput = _gather_class("InMemoryCreativeDirectorInput")
InMemoryDesignLanguageInput = _gather_class("InMemoryDesignLanguageInput")
InMemoryIAInput = _gather_class("InMemoryIAInput")
InMemoryUXInput = _gather_class("InMemoryUXInput")
InMemoryPsychologyInput = _gather_class("InMemoryPsychologyInput")
InMemoryBrandInput = _gather_class("InMemoryBrandInput")
InMemoryBusinessStrategyInput = _gather_class("InMemoryBusinessStrategyInput")

NullDesignSystemInput = _null_class("NullDesignSystemInput")
NullComponentIntelligenceInput = _null_class("NullComponentIntelligenceInput")
NullWireframeInput = _null_class("NullWireframeInput")
NullCreativeDirectorInput = _null_class("NullCreativeDirectorInput")
NullDesignLanguageInput = _null_class("NullDesignLanguageInput")
NullIAInput = _null_class("NullIAInput")
NullUXInput = _null_class("NullUXInput")
NullPsychologyInput = _null_class("NullPsychologyInput")
NullBrandInput = _null_class("NullBrandInput")
NullBusinessStrategyInput = _null_class("NullBusinessStrategyInput")


class InMemoryKnowledgeAdvisor:
    """A :class:`KnowledgeAdvisorPort` returning fixed knowledge signals."""

    def __init__(self, signals: Sequence[RawSignal] = ()) -> None:
        self._signals = tuple(signals)

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        return self._signals


class NullKnowledgeAdvisor:
    """A :class:`KnowledgeAdvisorPort` returning nothing."""

    async def advise(
        self, topics: Sequence[str], project: ProjectContext
    ) -> Sequence[RawSignal]:
        return ()
