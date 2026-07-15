"""The DS Graph primitive — the shared, traversable structure behind the six graphs.

Nodes are :class:`DSNode` s (typed by :class:`NodeKind`); edges are typed :class:`DSEdge` s.
The graph validates that every edge's endpoints exist and that the alias/derivation/dependency
relations (``ALIASES``, ``DERIVES_FROM``, ``DEPENDS_ON``) form no cycle — a token cannot
transitively alias or derive from itself, and a component cannot transitively depend on itself.
``USES``, ``HAS_VARIANT``, ``HAS_STATE``, ``THEMES``, ``CONSTRAINS`` and ``MAPS_TO`` are
directional but not required to be acyclic. This one primitive backs all six required graphs
(token, component, variant, theme, constraint, dependency).

Pure domain: standard library, the shared-kernel error base, DS ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.shared.ids import DSEdgeId, DSEvidenceId, DSNodeId
from design_system.domain.shared.value_objects import GraphKind, GraphRelation, NodeKind

__all__ = ["DSEdge", "DSGraph", "DSNode", "InvalidDSGraphError", "NodeNotFoundError"]

_ACYCLIC_RELATIONS = (
    GraphRelation.ALIASES,
    GraphRelation.DERIVES_FROM,
    GraphRelation.DEPENDS_ON,
)


class InvalidDSGraphError(DesignDirectorError):
    """Raised when a design-system graph is structurally invalid (dangling edge / cycle)."""

    code = "invalid_design_system_graph"
    http_status = 422


class NodeNotFoundError(DesignDirectorError):
    """Raised when a node is requested by an id absent from the graph."""

    code = "design_system_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class DSNode:
    """One node in a design-system graph.

    Attributes:
        id: Node identity.
        kind: The kind of thing the node represents.
        label: A short human-readable label (typically a token key or component name).
        evidence_ids: The evidence supporting the node.
    """

    id: DSNodeId
    kind: NodeKind
    label: str
    evidence_ids: tuple[DSEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidDSGraphError("DSNode.label must be non-empty.")
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class DSEdge:
    """A typed, directed edge between two design-system-graph nodes."""

    id: DSEdgeId
    source: DSNodeId
    target: DSNodeId
    relation: GraphRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidDSGraphError(
                "DSEdge cannot connect a node to itself.", details={"node": str(self.source)}
            )


@dataclass(frozen=True, slots=True)
class DSGraph:
    """An immutable, typed design-system graph."""

    kind: GraphKind
    nodes: Mapping[DSNodeId, DSNode] = field(default_factory=lambda: MappingProxyType({}))
    edges: tuple[DSEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise InvalidDSGraphError(
                    "Edge references a source node not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.nodes:
                raise InvalidDSGraphError(
                    "Edge references a target node not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        adjacency: dict[DSNodeId, list[DSNodeId]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.relation in _ACYCLIC_RELATIONS:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)

        def visit(node: DSNodeId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidDSGraphError(
                        "Alias/derivation/dependency relations form a cycle.",
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
        cls, kind: GraphKind, nodes: Iterable[DSNode], edges: Iterable[DSEdge] = ()
    ) -> DSGraph:
        """Build a graph from nodes and edges.

        Raises:
            InvalidDSGraphError: On a duplicate id, a dangling edge, or a cycle.
        """
        mapping: dict[DSNodeId, DSNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidDSGraphError(
                    "Duplicate node id in graph.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(kind=kind, nodes=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: DSNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: DSNodeId) -> DSNode:
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

    def by_kind(self, kind: NodeKind) -> tuple[DSNode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def successors(self, node_id: DSNodeId) -> tuple[DSNode, ...]:
        """The nodes this node points to (any relation)."""
        self.get(node_id)
        return tuple(self.nodes[e.target] for e in self.edges if e.source == node_id)

    def edges_from(self, node_id: DSNodeId) -> tuple[DSEdge, ...]:
        return tuple(e for e in self.edges if e.source == node_id)

    def evidence_ids(self) -> tuple[DSEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
