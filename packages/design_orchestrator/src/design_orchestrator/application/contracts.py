"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from any of the eleven
  upstream engines). The evidence consolidator turns these into cited
  :class:`~design_orchestrator.domain.evidence.evidence.DOEvidence`.
* :class:`OrchestrationInput` — the assembled input to a run: the brief, project, source refs,
  and every raw signal gathered.
* :class:`ExecutionDraft` — the planner's proposed per-page section plans (the ordered choices),
  citing evidence by id. The engine validates grounding, resolves the token/variant bindings,
  builds the layout, tree, and graphs, schedules reviews, scores, and assembles the plan.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from design_orchestrator.domain.context.context import (
    OrchestrationBrief,
    ProjectContext,
    SourceRefs,
)
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

__all__ = ["ExecutionDraft", "OrchestrationInput", "RawSignal"]


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
class OrchestrationInput:
    """The assembled input to an orchestration run."""

    brief: OrchestrationBrief
    project: ProjectContext
    source_refs: SourceRefs = field(default_factory=SourceRefs)
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class ExecutionDraft:
    """The planner's proposed plan — cited, awaiting resolution and assembly.

    Carries the ordered per-page section plans the planner decided. The engine resolves the
    token/variant bindings against the Design System, derives the layout, tree, and graphs,
    schedules the reviews, and assembles the versioned plan.
    """

    pages: tuple[PagePlan, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pages", tuple(self.pages))

    @property
    def sections(self) -> tuple:
        return tuple(s for page in self.pages for s in page.sections)
