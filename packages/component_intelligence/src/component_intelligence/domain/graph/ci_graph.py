"""The CI Graph primitive — the shared, traversable structure behind the two graphs.

Nodes are :class:`CINode` s (typed by :class:`NodeKind`); edges are typed :class:`CIEdge` s.
The graph validates that every edge's endpoints exist and that the containment/dependency
relations (``CONTAINS``, ``DEPENDS_ON``, ``REQUIRES``) form no cycle — a component cannot
transitively require or contain itself. ``CONFLICTS_WITH`` and ``ENHANCES`` may be mutual. This
one primitive backs both required graphs (component, dependency).

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEdgeId, CIEvidenceId, CINodeId
from component_intelligence.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["CIEdge", "CIGraph", "CINode", "InvalidCIGraphError", "NodeNotFoundError"]

_ACYCLIC_RELATIONS = (
    GraphRelation.CONTAINS,
    GraphRelation.DEPENDS_ON,
    GraphRelation.REQUIRES,
)


class InvalidCIGraphError(DesignDirectorError):
    """Raised when a component graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_component_intelligence_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "component_intelligence_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class CINode:
    """One node in a component graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label.
        evidence_ids: The evidence supporting the node.
    """

    id: CINodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidCIGraphError("CINode.label must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class CIEdge:
    """A typed, directed edge between two component-graph nodes."""

    id: CIEdgeId
    source: CINodeId
    target: CINodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidCIGraphError(
                "CIEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class CIGraph:
    """An immutable, typed component graph."""

    kind: GraphKind
    nodes: Mapping[CINodeId, CINode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[CIEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidCIGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidCIGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[CINodeId, list[CINodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.relation in _ACYCLIC_RELATIONS:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: CINodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidCIGraphError(
                        "Containment/dependency relations form a cycle.",
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
        cls, kind: GraphKind, nodes: Iterable[CINode], edges: Iterable[CIEdge] = ()
    ) -> CIGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidCIGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[CINodeId, CINode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidCIGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: CINodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: CINodeId) -> CINode:
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

    def by_kind(self, kind: NodeKind) -> tuple[CINode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: CINodeId) -> tuple[CINode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: CINodeId) -> tuple[CIEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
