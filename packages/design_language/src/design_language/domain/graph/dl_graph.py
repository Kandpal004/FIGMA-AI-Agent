"""The DL Graph primitive — the shared, traversable structure behind the two graphs.

Nodes are :class:`DLNode` s (typed by :class:`NodeKind`); edges are typed :class:`DLEdge` s.
The graph validates that every edge's endpoints exist and that the whole graph is acyclic — a
language derivation is a directed rationale (DNA → philosophy → token → constraint; archetype
→ traits; alternative → reason), never a cycle. This one primitive backs both required graphs
(visual, language), each an instance carrying the node kinds relevant to it.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEdgeId, DLEvidenceId, DLNodeId
from design_language.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["DLEdge", "DLGraph", "DLNode", "InvalidDLGraphError", "NodeNotFoundError"]


class InvalidDLGraphError(DesignDirectorError):
    """Raised when a design-language graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_design_language_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "design_language_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class DLNode:
    """One node in a design-language graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label.
        evidence_ids: The evidence supporting the node.
    """

    id: DLNodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidDLGraphError("DLNode.label must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class DLEdge:
    """A typed, directed edge between two design-language-graph nodes."""

    id: DLEdgeId
    source: DLNodeId
    target: DLNodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidDLGraphError(
                "DLEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class DLGraph:
    """An immutable, typed, acyclic design-language graph."""

    kind: GraphKind
    nodes: Mapping[DLNodeId, DLNode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[DLEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidDLGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidDLGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[DLNodeId, list[DLNodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: DLNodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidDLGraphError(
                        "Design-language graph relations form a cycle.",
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
        cls, kind: GraphKind, nodes: Iterable[DLNode], edges: Iterable[DLEdge] = ()
    ) -> DLGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidDLGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[DLNodeId, DLNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidDLGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: DLNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: DLNodeId) -> DLNode:
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

    def by_kind(self, kind: NodeKind) -> tuple[DLNode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: DLNodeId) -> tuple[DLNode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: DLNodeId) -> tuple[DLEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
