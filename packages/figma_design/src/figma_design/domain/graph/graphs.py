"""The five Figma graphs — the relational view of the design model.

A :class:`FigmaGraphs` bundle carries exactly the five graphs the engine must produce, each an
:class:`FDGraph` of the right :class:`GraphKind`:

* ``FIGMA_TREE`` — every node across pages and its ``CONTAINS`` structure.
* ``COMPONENT`` — component sets and their ``VARIANT_OF`` components, and instances ``INSTANCE_OF``
  their set.
* ``AUTO_LAYOUT`` — auto-layout frames and the children they lay out (``CONTAINS``).
* ``VARIABLE`` — collections, modes, variables, and their ``ALIASES`` / ``BINDS`` relations.
* ``STYLE`` — nodes ``USES_STYLE`` styles, and styles ``BINDS`` their backing variables.

Each graph is validated by the :class:`FDGraph` primitive (no dangling edges, acyclic containment/
variant/alias). The bundle only guarantees the right *kinds* are present.

Pure domain: standard library, the shared-kernel error base, the graph primitive, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.graph.fd_graph import FDGraph
from figma_design.domain.shared.ids import FDEvidenceId
from figma_design.domain.shared.value_objects import GraphKind

__all__ = ["FigmaGraphs", "InvalidGraphsError"]


class InvalidGraphsError(DesignDirectorError):
    """Raised when the five-graph bundle is malformed (wrong kind in a slot)."""

    code = "invalid_figma_design_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FigmaGraphs:
    """The five required Figma graphs.

    Attributes:
        figma_tree: The node containment graph across pages.
        component: The component-set / variant / instance graph.
        auto_layout: The auto-layout containment graph.
        variable: The variable collection / mode / alias / binding graph.
        style: The node-uses-style / style-binds-variable graph.
    """

    figma_tree: FDGraph
    component: FDGraph
    auto_layout: FDGraph
    variable: FDGraph
    style: FDGraph

    def __post_init__(self) -> None:
        expected = (
            (self.figma_tree, GraphKind.FIGMA_TREE),
            (self.component, GraphKind.COMPONENT),
            (self.auto_layout, GraphKind.AUTO_LAYOUT),
            (self.variable, GraphKind.VARIABLE),
            (self.style, GraphKind.STYLE),
        )
        for graph, kind in expected:
            if graph.kind is not kind:
                raise InvalidGraphsError(
                    f"Graph slot for {kind.value} holds a {graph.kind.value} graph.",
                    details={"expected": kind.value, "actual": graph.kind.value},
                )

    @property
    def all(self) -> tuple[FDGraph, ...]:
        return (self.figma_tree, self.component, self.auto_layout, self.variable, self.style)

    def get(self, kind: GraphKind) -> FDGraph:
        for graph in self.all:
            if graph.kind is kind:
                return graph
        raise InvalidGraphsError(f"No graph of kind {kind.value}.", details={"kind": kind.value})

    def evidence_ids(self) -> tuple[FDEvidenceId, ...]:
        return tuple(eid for graph in self.all for eid in graph.evidence_ids())

    @property
    def total_nodes(self) -> int:
        return sum(len(g) for g in self.all)
