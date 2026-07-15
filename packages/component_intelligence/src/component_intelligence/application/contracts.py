"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from any of the eleven
  upstream engines). The evidence consolidator turns these into cited
  :class:`~component_intelligence.domain.evidence.evidence.CIEvidence`.
* :class:`ComponentInput` — the assembled input to a run: the brief and project plus every raw
  signal gathered.
* :class:`CompositionDraft` — the brain's proposed component decisions and compatibility web,
  citing evidence by id. The engine validates grounding, resolves coherence, derives the rules
  and graphs, scores, and assembles the specification.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.domain.compatibility.compatibility import CompatibilitySet
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.context.context import CompositionBrief, ProjectContext
from component_intelligence.domain.shared.value_objects import ProvenanceKind

__all__ = ["CompositionDraft", "ComponentInput", "RawSignal"]


@dataclass(frozen=True, slots=True)
class RawSignal:
    """One neutral fact supplied by an input adapter.

    Attributes:
        provenance: Which source it came from.
        external_ref: Its id in that source (the audit anchor).
        claim: The crisp fact.
        confidence: Confidence in ``[0, 1]``.
        statement: Fuller supporting text, if any.
        source_name: A human-readable source label.
        tags: Free-form tags.
    """

    provenance: ProvenanceKind
    external_ref: str
    claim: str
    confidence: float = 0.7
    statement: str = ""
    source_name: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True, slots=True)
class ComponentInput:
    """The assembled input to a component-intelligence run."""

    brief: CompositionBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class CompositionDraft:
    """The brain's proposed composition — cited, awaiting coherence resolution and assembly."""

    composition: ComponentComposition
    compatibility: CompatibilitySet
