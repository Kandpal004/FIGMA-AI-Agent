"""The UX Graph primitive — the shared, traversable structure behind the five graphs.

Nodes are :class:`UXNode` s (typed by :class:`NodeKind`); edges are typed :class:`UXEdge`
s. The graph validates that every edge's endpoints exist and that the progression and
containment relations (``LEADS_TO``, ``PRECEDES``, ``DERIVES_FROM``, ``CONTAINS``) form no
cycle. ``CONFLICTS_WITH`` may be mutual. This one primitive backs all five required graphs
(decision, navigation, content hierarchy, trust hierarchy, interaction), each an instance
carrying the node kinds relevant to it — keeping the structure DRY and every graph
independently auditable.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEdgeId, UXEvidenceId, UXNodeId
from ux.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["InvalidUXGraphError", "NodeNotFoundError", "UXEdge", "UXGraph", "UXNode"]

_ACYCLIC_RELATIONS = (
    GraphRelation.LEADS_TO,
    GraphRelation.PRECEDES,
    GraphRelation.DERIVES_FROM,
    GraphRelation.CONTAINS,
)


class InvalidUXGraphError(DesignDirectorError):
    """Raised when a UX graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_ux_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "ux_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class UXNode:
    """One node in a UX graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label.
        evidence_ids: The evidence supporting the node.
    """

    id: UXNodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidUXGraphError("UXNode.label must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class UXEdge:
    """A typed, directed edge between two UX-graph nodes."""

    id: UXEdgeId
    source: UXNodeId
    target: UXNodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidUXGraphError(
                "UXEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class UXGraph:
    """An immutable, typed UX graph."""

    kind: GraphKind
    nodes: Mapping[UXNodeId, UXNode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[UXEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidUXGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidUXGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[UXNodeId, list[UXNodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.relation in _ACYCLIC_RELATIONS:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: UXNodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidUXGraphError(
                        "Progression/containment relations form a cycle.",
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
        cls, kind: GraphKind, nodes: Iterable[UXNode], edges: Iterable[UXEdge] = ()
    ) -> UXGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidUXGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[UXNodeId, UXNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidUXGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: UXNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: UXNodeId) -> UXNode:
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

    def by_kind(self, kind: NodeKind) -> tuple[UXNode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: UXNodeId) -> tuple[UXNode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: UXNodeId) -> tuple[UXEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
