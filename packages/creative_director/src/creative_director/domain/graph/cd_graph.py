"""The CD Graph primitive — the shared, traversable structure behind the five graphs.

Nodes are :class:`CDNode` s (typed by :class:`NodeKind`); edges are typed :class:`CDEdge` s.
The graph validates that every edge's endpoints exist and that the whole graph is acyclic — a
review is a directed audit (subject → dimension → finding → change → decision), never a cycle.
This one primitive backs all five required graphs (review, decision, approval, quality matrix,
improvement matrix), each an instance carrying the node kinds relevant to it — keeping the
structure DRY and every graph independently auditable.

Pure domain: standard library, the shared-kernel error base, CD ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from creative_director.domain.shared.ids import CDEdgeId, CDEvidenceId, CDNodeId
from creative_director.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["CDEdge", "CDGraph", "CDNode", "InvalidCDGraphError", "NodeNotFoundError"]


class InvalidCDGraphError(DesignDirectorError):
    """Raised when a review graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_creative_director_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "creative_director_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class CDNode:
    """One node in a review graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label.
        evidence_ids: The evidence supporting the node.
    """

    id: CDNodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple[CDEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidCDGraphError("CDNode.label must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class CDEdge:
    """A typed, directed edge between two review-graph nodes."""

    id: CDEdgeId
    source: CDNodeId
    target: CDNodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidCDGraphError(
                "CDEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class CDGraph:
    """An immutable, typed, acyclic review graph."""

    kind: GraphKind
    nodes: Mapping[CDNodeId, CDNode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[CDEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidCDGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidCDGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[CDNodeId, list[CDNodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: CDNodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidCDGraphError(
                        "Review graph relations form a cycle.",
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
        cls, kind: GraphKind, nodes: Iterable[CDNode], edges: Iterable[CDEdge] = ()
    ) -> CDGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidCDGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[CDNodeId, CDNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidCDGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: CDNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: CDNodeId) -> CDNode:
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

    def by_kind(self, kind: NodeKind) -> tuple[CDNode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: CDNodeId) -> tuple[CDNode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: CDNodeId) -> tuple[CDEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
