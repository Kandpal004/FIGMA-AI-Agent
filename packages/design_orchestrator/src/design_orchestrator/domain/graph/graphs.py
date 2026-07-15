"""The two orchestrator graphs — the relational view of the execution plan.

An :class:`OrchestratorGraphs` bundle carries exactly the two graphs the engine must produce,
each a :class:`DOGraph` of the right :class:`GraphKind`:

* ``EXECUTION`` — the ordered execution steps (setup tokens/theme, build page, place section,
  instantiate component, apply variant/responsive/accessibility, review gate) linked by
  ``PRECEDES`` / ``DEPENDS_ON``. Its topological order is the deterministic replay script a
  future Figma phase follows.
* ``LAYOUT`` — the layout regions linked by ``CONTAINS``, the containment hierarchy of the page.

Each graph is validated by the :class:`DOGraph` primitive (no dangling edges, acyclic ordering/
containment). The bundle only guarantees the right *kinds* are present.

Pure domain: standard library, the shared-kernel error base, the graph primitive, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_orchestrator.domain.graph.do_graph import DOGraph
from design_orchestrator.domain.shared.value_objects import GraphKind

__all__ = ["InvalidGraphsError", "OrchestratorGraphs"]


class InvalidGraphsError(DesignDirectorError):
    """Raised when the two-graph bundle is malformed (wrong kind in a slot)."""

    code = "invalid_design_orchestrator_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class OrchestratorGraphs:
    """The two required orchestrator graphs.

    Attributes:
        execution: The ordered execution-step graph (the replay script).
        layout: The layout-region containment graph.
    """

    execution: DOGraph
    layout: DOGraph

    def __post_init__(self) -> None:
        if self.execution.kind is not GraphKind.EXECUTION:
            raise InvalidGraphsError(
                f"Execution slot holds a {self.execution.kind.value} graph."
            )
        if self.layout.kind is not GraphKind.LAYOUT:
            raise InvalidGraphsError(f"Layout slot holds a {self.layout.kind.value} graph.")

    @property
    def all(self) -> tuple[DOGraph, ...]:
        return (self.execution, self.layout)

    def get(self, kind: GraphKind) -> DOGraph:
        for graph in self.all:
            if graph.kind is kind:
                return graph
        raise InvalidGraphsError(f"No graph of kind {kind.value}.", details={"kind": kind.value})

    def evidence_ids(self) -> tuple:
        return tuple(eid for graph in self.all for eid in graph.evidence_ids())

    @property
    def total_nodes(self) -> int:
        return sum(len(g) for g in self.all)
