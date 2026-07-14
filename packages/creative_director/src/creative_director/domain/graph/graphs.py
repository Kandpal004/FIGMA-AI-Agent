"""The five Creative Director graphs, grouped.

:class:`CreativeDirectorGraphs` bundles the engine's five required graphs — each a
:class:`CDGraph` instance keyed by its :class:`GraphKind`:

* **REVIEW** — subject → dimension → finding (what was inspected and found).
* **DECISION** — findings and gates → the decision; overrides supersede prior decisions.
* **APPROVAL** — hard gates → categories → the final approval node.
* **QUALITY_MATRIX** — categories → their scores (the quality picture, as a graph).
* **IMPROVEMENT_MATRIX** — required changes derived from their findings, ranked.

Pure domain: standard library, the shared-kernel error base, and the graph primitive.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.graph.cd_graph import CDGraph
from creative_director.domain.shared.ids import CDEvidenceId
from creative_director.domain.shared.value_objects import GraphKind

__all__ = ["CreativeDirectorGraphs", "InvalidGraphsError"]

_REQUIRED = frozenset(GraphKind)


class InvalidGraphsError(DesignDirectorError):
    """Raised when the set of graphs is incomplete or inconsistent."""

    code = "invalid_creative_director_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CreativeDirectorGraphs:
    """The engine's five graphs, one per :class:`GraphKind`."""

    graphs: tuple[CDGraph, ...]

    def __post_init__(self) -> None:
        by_kind: dict[GraphKind, CDGraph] = {}
        for graph in self.graphs:
            if graph.kind in by_kind:
                raise InvalidGraphsError(
                    "Duplicate graph kind.", details={"kind": graph.kind.value}
                )
            by_kind[graph.kind] = graph
        missing = _REQUIRED - by_kind.keys()
        if missing:
            raise InvalidGraphsError(
                "All five Creative Director graphs are required.",
                details={"missing": sorted(k.value for k in missing)},
            )
        object.__setattr__(self, "graphs", tuple(self.graphs))

    @classmethod
    def of(cls, graphs: Iterable[CDGraph]) -> CreativeDirectorGraphs:
        return cls(graphs=tuple(graphs))

    def get(self, kind: GraphKind) -> CDGraph:
        graph = next((g for g in self.graphs if g.kind is kind), None)
        if graph is None:  # pragma: no cover - guarded by the completeness invariant
            raise InvalidGraphsError(
                f"Graph {kind.value} not present.", details={"kind": kind.value}
            )
        return graph

    def all(self) -> tuple[CDGraph, ...]:
        return self.graphs

    def evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return tuple(eid for g in self.graphs for eid in g.evidence_ids())
