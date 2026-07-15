"""The two component graphs, grouped.

:class:`ComponentGraphs` bundles the engine's two required graphs — each a :class:`CIGraph`
instance keyed by its :class:`GraphKind`:

* **COMPONENT** — components contain their atomic sub-parts and are placed on pages.
* **DEPENDENCY** — the requires/depends-on/enhances/conflicts web between components.

Pure domain: standard library, the shared-kernel error base, and the graph primitive.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.graph.ci_graph import CIGraph
from component_intelligence.domain.shared.ids import CIEvidenceId
from component_intelligence.domain.shared.value_objects import GraphKind

__all__ = ["ComponentGraphs", "InvalidGraphsError"]

_REQUIRED = frozenset(GraphKind)


class InvalidGraphsError(DesignDirectorError):
    """Raised when the set of graphs is incomplete or inconsistent."""

    code = "invalid_component_intelligence_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentGraphs:
    """The engine's two graphs, one per :class:`GraphKind`."""

    graphs: tuple[CIGraph, ...]

    def __post_init__(self) -> None:
        by_kind: dict[GraphKind, CIGraph] = {}
        for graph in self.graphs:
            if graph.kind in by_kind:
                raise InvalidGraphsError(
                    "Duplicate graph kind.", details={"kind": graph.kind.value}
                )
            by_kind[graph.kind] = graph
        missing = _REQUIRED - by_kind.keys()
        if missing:
            raise InvalidGraphsError(
                "Both component graphs are required.",
                details={"missing": sorted(k.value for k in missing)},
            )
        object.__setattr__(self, "graphs", tuple(self.graphs))

    @classmethod
    def of(cls, graphs: Iterable[CIGraph]) -> ComponentGraphs:
        return cls(graphs=tuple(graphs))

    def get(self, kind: GraphKind) -> CIGraph:
        graph = next((g for g in self.graphs if g.kind is kind), None)
        if graph is None:  # pragma: no cover - guarded by the completeness invariant
            raise InvalidGraphsError(
                f"Graph {kind.value} not present.", details={"kind": kind.value}
            )
        return graph

    def all(self) -> tuple[CIGraph, ...]:
        return self.graphs

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for g in self.graphs for eid in g.evidence_ids())
