"""The WF Graph primitive — the shared, traversable structure behind the six graphs.

Nodes are :class:`WFNode` s (typed by :class:`NodeKind`); edges are typed :class:`WFEdge` s.
The graph validates that every edge's endpoints exist and that the containment/ordering/
dependency relations (``CONTAINS``, ``ORDERED_BEFORE``, ``DEPENDS_ON``, ``REQUIRES``,
``COMPOSES``, ``GATES``) form no cycle — a cyclic build or approval plan is not executable.
``PRODUCES`` and ``CONSUMES`` wire sections to the data/assets flowing between them. This one
primitive backs all six required graphs (wireframe, section-dependency, content, component,
execution, approval), each an instance carrying the node kinds relevant to it — keeping the
structure DRY and every graph independently auditable.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from wireframe.domain.shared.ids import WFEdgeId, WFEvidenceId, WFNodeId
from wireframe.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["InvalidWFGraphError", "NodeNotFoundError", "WFEdge", "WFGraph", "WFNode"]

_ACYCLIC_RELATIONS = (
    GraphRelation.CONTAINS,
    GraphRelation.ORDERED_BEFORE,
    GraphRelation.DEPENDS_ON,
    GraphRelation.REQUIRES,
    GraphRelation.COMPOSES,
    GraphRelation.GATES,
)


class InvalidWFGraphError(DesignDirectorError):
    """Raised when a wireframe graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_wireframe_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "wireframe_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class WFNode:
    """One node in a wireframe-planning graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label.
        evidence_ids: The evidence supporting the node.
    """

    id: WFNodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidWFGraphError("WFNode.label must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class WFEdge:
    """A typed, directed edge between two wireframe-graph nodes."""

    id: WFEdgeId
    source: WFNodeId
    target: WFNodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidWFGraphError(
                "WFEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class WFGraph:
    """An immutable, typed wireframe-planning graph."""

    kind: GraphKind
    nodes: Mapping[WFNodeId, WFNode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[WFEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidWFGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidWFGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[WFNodeId, list[WFNodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.relation in _ACYCLIC_RELATIONS:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: WFNodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidWFGraphError(
                        "Containment/ordering/dependency relations form a cycle.",
                        details={"node": str(nxt), "graph": self.kind.value},
                    )
                if colour[nxt] == WHITE:
                    visit(nxt)
            colour[node] = BLACK

        for node in self.nodes:
            if colour[node] == WHITE:
                visit(node)

    @classmethod
    def of(
        cls, kind: GraphKind, nodes: Iterable[WFNode], edges: Iterable[WFEdge] = ()
    ) -> WFGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidWFGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[WFNodeId, WFNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidWFGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: WFNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: WFNodeId) -> WFNode:
        """Return the node for ``node_id``.

        Raises:
            NodeNotFoundError: If no such node exists.
        """
        node = self.nodes.get(node_id)
        if node is None:
            raise NodeNotFoundError(
                f"Node {node_id} not found.", details={"node_id": str(node_id)}
            )
        return node

    def by_kind(self, kind: NodeKind) -> tuple[WFNode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: WFNodeId) -> tuple[WFNode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: WFNodeId) -> tuple[WFEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
