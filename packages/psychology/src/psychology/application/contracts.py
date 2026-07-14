"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine or
downstream consumer:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from Brand Strategy,
  Business Strategy, Knowledge, Research, Competitor, or Reasoning). The evidence
  consolidator turns these into cited
  :class:`~psychology.domain.evidence.evidence.PsychologyEvidence`.
* :class:`PsychologyInput` — the assembled input to a run: the brief and project plus
  every raw signal gathered.
* :class:`PsychologyDraft` — the psychologist's proposed *content* (profile, personas,
  jobs, journeys, the judgement-bearing matrix inputs, and the framework applications),
  already citing evidence by id. The engine validates, builds the matrices/frameworks/
  graphs, scores, and assembles the report.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from psychology.domain.context.context import ProjectContext, PsychologyBrief
from psychology.domain.frameworks.behavioral_economics import BehavioralPrincipleSet
from psychology.domain.frameworks.hook import HookLoop
from psychology.domain.frameworks.maslow import MaslowMapping
from psychology.domain.journey.buying_journey import BuyingJourney
from psychology.domain.journey.decision_journey import DecisionJourney
from psychology.domain.matrices.cells import (
    BehaviorCell,
    ObjectionCell,
    RetentionCell,
    ValueCell,
)
from psychology.domain.persona.buying_persona import BuyingPersonaSet
from psychology.domain.persona.jtbd import JTBDSet
from psychology.domain.persona.persona import PersonaSet
from psychology.domain.shared.value_objects import ProvenanceKind
from psychology.domain.state.profile import PsychologicalProfile

__all__ = ["PsychologyDraft", "PsychologyInput", "RawSignal"]


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
class PsychologyInput:
    """The assembled input to a psychology run."""

    brief: PsychologyBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class PsychologyDraft:
    """The psychologist's proposed content — cited, awaiting validation and assembly."""

    profile: PsychologicalProfile
    personas: PersonaSet
    buying_personas: BuyingPersonaSet
    jobs: JTBDSet
    buying_journey: BuyingJourney
    decision_journey: DecisionJourney
    objections: tuple[ObjectionCell, ...] = ()
    behaviors: tuple[BehaviorCell, ...] = ()
    value_cells: tuple[ValueCell, ...] = ()
    retention_cells: tuple[RetentionCell, ...] = ()
    maslow: MaslowMapping | None = None
    hook: HookLoop | None = None
    principles: BehavioralPrincipleSet = BehavioralPrincipleSet()

    def __post_init__(self) -> None:
        object.__setattr__(self, "objections", tuple(self.objections))
        object.__setattr__(self, "behaviors", tuple(self.behaviors))
        object.__setattr__(self, "value_cells", tuple(self.value_cells))
        object.__setattr__(self, "retention_cells", tuple(self.retention_cells))
