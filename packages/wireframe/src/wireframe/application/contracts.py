"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine or
downstream consumer:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from Information
  Architecture, UX, Business Strategy, Brand, Psychology, Knowledge, Research, Competitor, or
  Reasoning). The evidence consolidator turns these into cited
  :class:`~wireframe.domain.evidence.evidence.WFEvidence`.
* :class:`WireframeInput` — the assembled input to a run: the brief and project plus every
  raw signal gathered.
* :class:`WireframeDraft` — the planner's proposed structure (the page/section blueprint,
  sections already carrying their blocks, components, requirements, criteria, checklist, and
  per-section approval requirement), citing evidence by id. The engine validates, resolves
  execution order, wires approvals, builds the six graphs, scores, and assembles the plan.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from wireframe.domain.context.context import ProjectContext, WireframeBrief
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.shared.value_objects import ProvenanceKind

__all__ = ["RawSignal", "WireframeDraft", "WireframeInput"]


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
class WireframeInput:
    """The assembled input to a wireframe-planning run."""

    brief: WireframeBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class WireframeDraft:
    """The planner's proposed structure — cited, awaiting validation and assembly.

    The blueprint's sections carry their blocks, components, requirements, criteria, review
    checklist, and per-section approval requirement. Execution order and approval dependency
    wiring are resolved by the pipeline, not the planner.
    """

    blueprint: PlanBlueprint
