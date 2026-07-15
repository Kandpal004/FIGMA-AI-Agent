"""The six design-system graphs — the relational view of the specification.

A :class:`DesignSystemGraphs` bundle carries exactly the six graphs the engine must produce,
each a :class:`DSGraph` of the right :class:`GraphKind`:

* ``TOKEN`` — tokens and their ``ALIASES`` / ``DERIVES_FROM`` relationships (the three tiers).
* ``COMPONENT`` — components and the tokens they ``USES``.
* ``VARIANT`` — components and their ``HAS_VARIANT`` / ``HAS_STATE`` structure.
* ``THEME`` — themes and the tokens they ``THEMES``.
* ``CONSTRAINT`` — constraints and what they ``CONSTRAINS``.
* ``DEPENDENCY`` — components and their ``DEPENDS_ON`` closure.

Each graph is validated by the :class:`DSGraph` primitive (no dangling edges, acyclic alias/
derivation/dependency relations). The bundle only guarantees the right *kinds* are present and
each slot holds a graph of its declared kind.

Pure domain: standard library, the shared-kernel error base, the graph primitive, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_system.domain.graph.ds_graph import DSGraph
from design_system.domain.shared.ids import DSEvidenceId
from design_system.domain.shared.value_objects import GraphKind

__all__ = ["DesignSystemGraphs", "InvalidGraphsError"]


class InvalidGraphsError(DesignDirectorError):
    """Raised when the six-graph bundle is malformed (wrong kind in a slot)."""

    code = "invalid_design_system_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DesignSystemGraphs:
    """The six required design-system graphs.

    Attributes:
        token: The token graph (alias/derivation across the three tiers).
        component: The component→token usage graph.
        variant: The component→variant/state structure graph.
        theme: The theme→token theming graph.
        constraint: The constraint→target graph.
        dependency: The component dependency-closure graph.
    """

    token: DSGraph
    component: DSGraph
    variant: DSGraph
    theme: DSGraph
    constraint: DSGraph
    dependency: DSGraph

    def __post_init__(self) -> None:
        expected = (
            (self.token, GraphKind.TOKEN),
            (self.component, GraphKind.COMPONENT),
            (self.variant, GraphKind.VARIANT),
            (self.theme, GraphKind.THEME),
            (self.constraint, GraphKind.CONSTRAINT),
            (self.dependency, GraphKind.DEPENDENCY),
        )
        for graph, kind in expected:
            if graph.kind is not kind:
                raise InvalidGraphsError(
                    f"Graph slot for {kind.value} holds a {graph.kind.value} graph.",
                    details={"expected": kind.value, "actual": graph.kind.value},
                )

    @property
    def all(self) -> tuple[DSGraph, ...]:
        return (
            self.token,
            self.component,
            self.variant,
            self.theme,
            self.constraint,
            self.dependency,
        )

    def get(self, kind: GraphKind) -> DSGraph:
        for graph in self.all:
            if graph.kind is kind:
                return graph
        raise InvalidGraphsError(f"No graph of kind {kind.value}.", details={"kind": kind.value})

    def evidence_ids(self) -> tuple[DSEvidenceId, ...]:
        return tuple(eid for graph in self.all for eid in graph.evidence_ids())

    @property
    def total_nodes(self) -> int:
        return sum(len(g) for g in self.all)
