"""In-memory input adapters — scriptable stand-ins for the signal ports.

These implement the six input ports with pre-supplied :class:`RawSignal` s, so the engine runs and
is tested with no upstream engines wired. They are the honest default for local running and tests
(a stand-in for the real Phase 3 / 13 / 14 / 15 / 16 / 17 adapters). A null adapter returns
nothing.
"""

from __future__ import annotations

from collections.abc import Sequence

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext

__all__ = [
    "InMemoryComponentIntelligenceInput",
    "InMemoryCreativeDirectorInput",
    "InMemoryDesignLanguageInput",
    "InMemoryDesignOrchestratorInput",
    "InMemoryDesignSystemInput",
    "InMemoryKnowledgeAdvisor",
    "NullComponentIntelligenceInput",
    "NullCreativeDirectorInput",
    "NullDesignLanguageInput",
    "NullDesignOrchestratorInput",
    "NullDesignSystemInput",
    "NullKnowledgeAdvisor",
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


InMemoryDesignOrchestratorInput = _gather_class("InMemoryDesignOrchestratorInput")
InMemoryDesignSystemInput = _gather_class("InMemoryDesignSystemInput")
InMemoryComponentIntelligenceInput = _gather_class("InMemoryComponentIntelligenceInput")
InMemoryDesignLanguageInput = _gather_class("InMemoryDesignLanguageInput")
InMemoryCreativeDirectorInput = _gather_class("InMemoryCreativeDirectorInput")

NullDesignOrchestratorInput = _null_class("NullDesignOrchestratorInput")
NullDesignSystemInput = _null_class("NullDesignSystemInput")
NullComponentIntelligenceInput = _null_class("NullComponentIntelligenceInput")
NullDesignLanguageInput = _null_class("NullDesignLanguageInput")
NullCreativeDirectorInput = _null_class("NullCreativeDirectorInput")


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
