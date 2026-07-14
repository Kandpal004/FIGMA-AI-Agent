"""The six psychology graphs, grouped.

:class:`PsychologyGraphs` holds the six required graphs — Customer Decision, Emotion,
Trust, Objection, Motivation, and Behavior — each a :class:`PsychGraph` of the relevant
node kinds. Grouping them keeps the report aggregate clean and lets the facade resolve a
graph by :class:`GraphKind`.

Pure domain: standard library and the graph primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from psychology.domain.graph.psych_graph import PsychGraph
from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import GraphKind

__all__ = ["PsychologyGraphs"]


def _empty(kind: GraphKind) -> PsychGraph:
    return PsychGraph(kind=kind)


@dataclass(frozen=True, slots=True)
class PsychologyGraphs:
    """The six psychology graphs, grouped."""

    decision: PsychGraph = field(default_factory=lambda: _empty(GraphKind.DECISION))
    emotion: PsychGraph = field(default_factory=lambda: _empty(GraphKind.EMOTION))
    trust: PsychGraph = field(default_factory=lambda: _empty(GraphKind.TRUST))
    objection: PsychGraph = field(default_factory=lambda: _empty(GraphKind.OBJECTION))
    motivation: PsychGraph = field(default_factory=lambda: _empty(GraphKind.MOTIVATION))
    behavior: PsychGraph = field(default_factory=lambda: _empty(GraphKind.BEHAVIOR))

    def __post_init__(self) -> None:
        for name, expected in (
            ("decision", GraphKind.DECISION), ("emotion", GraphKind.EMOTION),
            ("trust", GraphKind.TRUST), ("objection", GraphKind.OBJECTION),
            ("motivation", GraphKind.MOTIVATION), ("behavior", GraphKind.BEHAVIOR),
        ):
            graph = getattr(self, name)
            if graph.kind is not expected:
                raise ValueError(f"PsychologyGraphs.{name} must be a {expected.value} graph.")

    def get(self, kind: GraphKind) -> PsychGraph:
        return {
            GraphKind.DECISION: self.decision,
            GraphKind.EMOTION: self.emotion,
            GraphKind.TRUST: self.trust,
            GraphKind.OBJECTION: self.objection,
            GraphKind.MOTIVATION: self.motivation,
            GraphKind.BEHAVIOR: self.behavior,
        }[kind]

    def all(self) -> tuple[PsychGraph, ...]:
        return (
            self.decision, self.emotion, self.trust,
            self.objection, self.motivation, self.behavior,
        )

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for g in self.all() for eid in g.evidence_ids())
