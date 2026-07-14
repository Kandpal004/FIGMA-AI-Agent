"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine or
downstream consumer:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from Psychology, Brand
  Strategy, Business Strategy, Knowledge, Research, Competitor, or Reasoning). The
  evidence consolidator turns these into cited
  :class:`~ux.domain.evidence.evidence.UXEvidence`.
* :class:`UXInput` — the assembled input to a run: the brief and project plus every raw
  signal gathered.
* :class:`UXDraft` — the strategist's proposed *content* (goals, mental model, page
  strategies, journeys, flows, and the six strategies), already citing evidence by id. The
  engine validates, builds the analyses/laws/graphs, scores, and assembles the report.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from ux.domain.context.context import ProjectContext, UXBrief
from ux.domain.flow.flow import FlowSet
from ux.domain.goals.goal import GoalSet
from ux.domain.goals.mental_model import MentalModel
from ux.domain.journey.journeys import JourneyMap
from ux.domain.page.page_strategy import PageStrategySet
from ux.domain.shared.value_objects import ProvenanceKind
from ux.domain.strategy.strategies import UXStrategies

__all__ = ["RawSignal", "UXDraft", "UXInput"]


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
class UXInput:
    """The assembled input to a UX strategy run."""

    brief: UXBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class UXDraft:
    """The strategist's proposed content — cited, awaiting validation and assembly."""

    goals: GoalSet
    mental_model: MentalModel
    pages: PageStrategySet
    journeys: JourneyMap
    flows: FlowSet
    strategies: UXStrategies
