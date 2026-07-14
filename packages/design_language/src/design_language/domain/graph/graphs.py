"""The two design-language graphs, grouped.

:class:`DesignLanguageGraphs` bundles the engine's two required graphs — each a
:class:`DLGraph` instance keyed by its :class:`GraphKind`:

* **VISUAL** — DNA → philosophies → tokens/systems → constraints (how the language is built).
* **LANGUAGE** — the selected archetype → its influences/traits, and the considered
  alternatives → their rejection reasons (why this language, not those).

Pure domain: standard library, the shared-kernel error base, and the graph primitive.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.graph.dl_graph import DLGraph
from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import GraphKind

__all__ = ["DesignLanguageGraphs", "InvalidGraphsError"]

_REQUIRED = frozenset(GraphKind)


class InvalidGraphsError(DesignDirectorError):
    """Raised when the set of graphs is incomplete or inconsistent."""

    code = "invalid_design_language_graphs"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DesignLanguageGraphs:
    """The engine's two graphs, one per :class:`GraphKind`."""

    graphs: tuple[DLGraph, ...]

    def __post_init__(self) -> None:
        by_kind: dict[GraphKind, DLGraph] = {}
        for graph in self.graphs:
            if graph.kind in by_kind:
                raise InvalidGraphsError(
                    "Duplicate graph kind.", details={"kind": graph.kind.value}
                )
            by_kind[graph.kind] = graph
        missing = _REQUIRED - by_kind.keys()
        if missing:
            raise InvalidGraphsError(
                "Both design-language graphs are required.",
                details={"missing": sorted(k.value for k in missing)},
            )
        object.__setattr__(self, "graphs", tuple(self.graphs))

    @classmethod
    def of(cls, graphs: Iterable[DLGraph]) -> DesignLanguageGraphs:
        return cls(graphs=tuple(graphs))

    def get(self, kind: GraphKind) -> DLGraph:
        graph = next((g for g in self.graphs if g.kind is kind), None)
        if graph is None:  # pragma: no cover - guarded by the completeness invariant
            raise InvalidGraphsError(
                f"Graph {kind.value} not present.", details={"kind": kind.value}
            )
        return graph

    def all(self) -> tuple[DLGraph, ...]:
        return self.graphs

    def evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(eid for g in self.graphs for eid in g.evidence_ids())
