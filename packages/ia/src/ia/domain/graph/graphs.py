"""The six IA graphs, grouped.

:class:`IAGraphs` holds the six required graphs — Site Map, Navigation, Page, Section,
Relationship, and Content Tree — each an :class:`IAGraph` of the relevant node kinds.
Grouping them keeps the report aggregate clean and lets the facade resolve a graph by
:class:`GraphKind`.

Pure domain: standard library and the graph primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ia.domain.graph.ia_graph import IAGraph
from ia.domain.shared.ids import IAEvidenceId
from ia.domain.shared.value_objects import GraphKind

__all__ = ["IAGraphs"]


def _empty(kind: GraphKind) -> IAGraph:
    return IAGraph(kind=kind)


@dataclass(frozen=True, slots=True)
class IAGraphs:
    """The six IA graphs, grouped."""

    sitemap: IAGraph = field(default_factory=lambda: _empty(GraphKind.SITEMAP))
    navigation: IAGraph = field(default_factory=lambda: _empty(GraphKind.NAVIGATION))
    page: IAGraph = field(default_factory=lambda: _empty(GraphKind.PAGE))
    section: IAGraph = field(default_factory=lambda: _empty(GraphKind.SECTION))
    relationship: IAGraph = field(default_factory=lambda: _empty(GraphKind.RELATIONSHIP))
    content_tree: IAGraph = field(default_factory=lambda: _empty(GraphKind.CONTENT_TREE))

    def __post_init__(self) -> None:
        for name, expected in (
            ("sitemap", GraphKind.SITEMAP), ("navigation", GraphKind.NAVIGATION),
            ("page", GraphKind.PAGE), ("section", GraphKind.SECTION),
            ("relationship", GraphKind.RELATIONSHIP), ("content_tree", GraphKind.CONTENT_TREE),
        ):
            graph = getattr(self, name)
            if graph.kind is not expected:
                raise ValueError(f"IAGraphs.{name} must be a {expected.value} graph.")

    def get(self, kind: GraphKind) -> IAGraph:
        return {
            GraphKind.SITEMAP: self.sitemap,
            GraphKind.NAVIGATION: self.navigation,
            GraphKind.PAGE: self.page,
            GraphKind.SECTION: self.section,
            GraphKind.RELATIONSHIP: self.relationship,
            GraphKind.CONTENT_TREE: self.content_tree,
        }[kind]

    def all(self) -> tuple[IAGraph, ...]:
        return (
            self.sitemap, self.navigation, self.page,
            self.section, self.relationship, self.content_tree,
        )

    def evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return tuple(eid for g in self.all() for eid in g.evidence_ids())
