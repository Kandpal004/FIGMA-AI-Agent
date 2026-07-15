"""The DO Graph primitive — the shared, traversable structure behind both graphs.

Nodes are :class:`DONode` s (typed by :class:`NodeKind`); edges are typed :class:`DOEdge` s. The
graph validates that every edge's endpoints exist and that the ordering/containment relations
(``PRECEDES``, ``DEPENDS_ON``, ``CONTAINS``) form no cycle — the execution order and the region
containment are acyclic, so a deterministic topological order always exists. ``PLACES`` and
``BINDS`` are directional but not required to be acyclic. This one primitive backs both required
graphs (execution, layout).

Pure domain: standard library, the shared-kernel error base, DO ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.ids import DOEdgeId, DONodeId
from design_orchestrator.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["DOEdge", "DOGraph", "DONode", "InvalidDOGraphError", "NodeNotFoundError"]

_ACYCLIC_RELATIONS = (
    GraphRelation.PRECEDES,
    GraphRelation.DEPENDS_ON,
    GraphRelation.CONTAINS,
)


class InvalidDOGraphError(DesignDirectorError):
    """Raised when an orchestrator graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_design_orchestrator_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "design_orchestrator_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class DONode:
    """One node in an orchestrator graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label.
        evidence_ids: The evidence supporting the node.
    """

    id: DONodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidDOGraphError("DONode.label must be non-empty.")
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class DOEdge:
    """A typed, directed edge between two orchestrator-graph nodes."""

    id: DOEdgeId
    source: DONodeId
    target: DONodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidDOGraphError(
                "DOEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class DOGraph:
    """An immutable, typed orchestrator graph."""

    kind: GraphKind
    nodes: Mapping[DONodeId, DONode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[DOEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidDOGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidDOGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[DONodeId, list[DONodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.relation in _ACYCLIC_RELATIONS:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: DONodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidDOGraphError(
                        "Ordering/containment relations form a cycle.",
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
        cls, kind: GraphKind, nodes: Iterable[DONode], edges: Iterable[DOEdge] = ()
    ) -> DOGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidDOGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[DONodeId, DONode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidDOGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: DONodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: DONodeId) -> DONode:
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

    def by_kind(self, kind: NodeKind) -> tuple[DONode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: DONodeId) -> tuple[DONode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: DONodeId) -> tuple[DOEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def topological_order(self) -> tuple[DONode, ...]:
        """A deterministic topological order over the acyclic relations.

        Kahn's algorithm with a stable tie-break on ``(kind, label)``, so the same graph always
        yields the same order — the execution sequence a future Figma phase replays.
        """
        adjacency: dict[DONodeId, list[DONodeId]] = {n: [] for n in self.nodes}
        indegree: dict[DONodeId, int] = dict.fromkeys(self.nodes, 0)
        for edge in self.edges:
            if edge.relation in _ACYCLIC_RELATIONS:
                adjacency[edge.source].append(edge.target)
                indegree[edge.target] += 1

        def sort_key(node_id: DONodeId) -> tuple[str, str, str]:
            node = self.nodes[node_id]
            return (node.kind.value, node.label, str(node_id))

        ready = sorted((n for n, d in indegree.items() if d == 0), key=sort_key)
        order: list[DONode] = []
        while ready:
            node_id = ready.pop(0)
            order.append(self.nodes[node_id])
            for nxt in adjacency[node_id]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)
            ready.sort(key=sort_key)
        return tuple(order)

    def evidence_ids(self) -> tuple:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
