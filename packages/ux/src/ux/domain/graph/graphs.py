"""The five UX graphs, grouped.

:class:`UXGraphs` holds the five required graphs — UX Decision, Navigation, Content
Hierarchy, Trust Hierarchy, and Interaction — each a :class:`UXGraph` of the relevant node
kinds. Grouping them keeps the report aggregate clean and lets the facade resolve a graph
by :class:`GraphKind`.

Pure domain: standard library and the graph primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ux.domain.graph.ux_graph import UXGraph
from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import GraphKind

__all__ = ["UXGraphs"]


def _empty(kind: GraphKind) -> UXGraph:
    return UXGraph(kind=kind)


@dataclass(frozen=True, slots=True)
class UXGraphs:
    """The five UX graphs, grouped."""

    decision: UXGraph = field(default_factory=lambda: _empty(GraphKind.DECISION))
    navigation: UXGraph = field(default_factory=lambda: _empty(GraphKind.NAVIGATION))
    content_hierarchy: UXGraph = field(
        default_factory=lambda: _empty(GraphKind.CONTENT_HIERARCHY)
    )
    trust_hierarchy: UXGraph = field(
        default_factory=lambda: _empty(GraphKind.TRUST_HIERARCHY)
    )
    interaction: UXGraph = field(default_factory=lambda: _empty(GraphKind.INTERACTION))

    def __post_init__(self) -> None:
        for name, expected in (
            ("decision", GraphKind.DECISION), ("navigation", GraphKind.NAVIGATION),
            ("content_hierarchy", GraphKind.CONTENT_HIERARCHY),
            ("trust_hierarchy", GraphKind.TRUST_HIERARCHY),
            ("interaction", GraphKind.INTERACTION),
        ):
            graph = getattr(self, name)
            if graph.kind is not expected:
                raise ValueError(f"UXGraphs.{name} must be a {expected.value} graph.")

    def get(self, kind: GraphKind) -> UXGraph:
        return {
            GraphKind.DECISION: self.decision,
            GraphKind.NAVIGATION: self.navigation,
            GraphKind.CONTENT_HIERARCHY: self.content_hierarchy,
            GraphKind.TRUST_HIERARCHY: self.trust_hierarchy,
            GraphKind.INTERACTION: self.interaction,
        }[kind]

    def all(self) -> tuple[UXGraph, ...]:
        return (
            self.decision, self.navigation, self.content_hierarchy,
            self.trust_hierarchy, self.interaction,
        )

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for g in self.all() for eid in g.evidence_ids())
