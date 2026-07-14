"""The six wireframe-planning graphs, grouped.

:class:`WireframeGraphs` bundles the engine's six required graphs — each a :class:`WFGraph`
instance keyed by its :class:`GraphKind`:

* **WIREFRAME** — the master tree: page contains sections contains blocks.
* **SECTION_DEPENDENCY** — which sections must be built before which (acyclic).
* **CONTENT** — sections to their blocks to the data/assets they need.
* **COMPONENT** — sections to the components they require, and component composition.
* **EXECUTION** — the deterministic build order (sections ordered before one another).
* **APPROVAL** — the approval gates and their sign-off dependencies.

Pure domain: standard library, the shared-kernel error base, and the graph primitive.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.graph.wf_graph import WFGraph
from wireframe.domain.shared.ids import WFEvidenceId
from wireframe.domain.shared.value_objects import GraphKind

__all__ = ["InvalidWireframeGraphsError", "WireframeGraphs"]

_REQUIRED = frozenset(GraphKind)


class InvalidWireframeGraphsError(DesignDirectorError):
    """Raised when the set of graphs is incomplete or inconsistent."""

    code = "invalid_wireframe_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class WireframeGraphs:
    """The engine's six graphs, one per :class:`GraphKind`."""

    graphs: tuple[WFGraph, ...]

    def __post_init__(self) -> None:
        by_kind: dict[GraphKind, WFGraph] = {}
        for graph in self.graphs:
            if graph.kind in by_kind:
                raise InvalidWireframeGraphsError(
                    "Duplicate graph kind.", details={"kind": graph.kind.value}
                )
            by_kind[graph.kind] = graph
        missing = _REQUIRED - by_kind.keys()
        if missing:
            raise InvalidWireframeGraphsError(
                "All six wireframe graphs are required.",
                details={"missing": sorted(k.value for k in missing)},
            )
        object.__setattr__(self, "graphs", tuple(self.graphs))

    @classmethod
    def of(cls, graphs: Iterable[WFGraph]) -> WireframeGraphs:
        return cls(graphs=tuple(graphs))

    def get(self, kind: GraphKind) -> WFGraph:
        graph = next((g for g in self.graphs if g.kind is kind), None)
        if graph is None:  # pragma: no cover - guarded by the completeness invariant
            raise InvalidWireframeGraphsError(
                f"Graph {kind.value} not present.", details={"kind": kind.value}
            )
        return graph

    def all(self) -> tuple[WFGraph, ...]:
        return self.graphs

    def evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return tuple(eid for g in self.graphs for eid in g.evidence_ids())
