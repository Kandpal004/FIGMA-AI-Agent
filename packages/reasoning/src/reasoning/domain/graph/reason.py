"""The Reason Graph — the engine's structured chain of inference.

A :class:`ReasonNode` is one step of reasoning: a strategic *question*, the
*conclusion* the engine reached, the evidence that supports it, and the prior
reasons it builds on. A :class:`ReasonGraph` links these into a directed acyclic
graph of ``premise → conclusion`` edges, so *why* the engine concluded anything
can be reconstructed by walking premises down to cited evidence.

Two kinds of node coexist, deliberately:

* **Premise nodes** (no premises of their own) are *givens* — a business goal from
  the brief, a prior approved decision the strategy must respect. They may
  legitimately carry no evidence; they are inputs, not claims.
* **Inference nodes** build on premises and/or cite evidence.

Acyclicity is guaranteed *by construction*: a node may be added only once every
premise it names already exists in the graph. There is no way to introduce a
forward reference or a cycle. Evidence ids are validated against the strategy's
:class:`EvidenceGraph` at assembly time (the aggregate's job), so this module
depends only on the evidence *id* type, not the evidence graph — keeping the two
graphs independent.

Testing considerations
----------------------
* :class:`ReasonNode` validates a non-empty question/conclusion and a confidence
  within ``[0, 1]``; it is immutable.
* Adding a node whose premise is absent, or whose id already exists, raises
  :class:`InvalidReasonGraphError`; this makes cycles impossible.
* :meth:`ReasonGraph.ancestors` returns the transitive premise closure in a
  deterministic order.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import EvidenceId, ReasonNodeId
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = [
    "InvalidReasonGraphError",
    "ReasonGraph",
    "ReasonNode",
    "ReasonNodeNotFoundError",
]


class InvalidReasonGraphError(DesignDirectorError):
    """Raised when a reason node or graph edge is invalid."""

    code = "invalid_reason_graph"
    http_status = 422


class ReasonNodeNotFoundError(DesignDirectorError):
    """Raised when a reason node is requested by an id absent from the graph."""

    code = "reason_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class ReasonNode:
    """One inference step in the reason graph.

    Attributes:
        id: Node identity.
        dimension: The strategy dimension this reasoning concerns.
        question: The strategic question being answered.
        conclusion: The conclusion the engine reached.
        confidence: Confidence in this inference, in ``[0, 1]``.
        evidence_ids: Supporting evidence (resolved against the EvidenceGraph).
        premise_ids: Prior reasons this conclusion builds on.
    """

    id: ReasonNodeId
    dimension: ReasoningDimension
    question: str
    conclusion: str
    confidence: float
    evidence_ids: tuple[EvidenceId, ...] = ()
    premise_ids: tuple[ReasonNodeId, ...] = ()

    def __post_init__(self) -> None:
        if not self.question or not self.question.strip():
            raise InvalidReasonGraphError("ReasonNode.question must be non-empty.")
        if not self.conclusion or not self.conclusion.strip():
            raise InvalidReasonGraphError("ReasonNode.conclusion must be non-empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidReasonGraphError(
                "ReasonNode.confidence must be within [0, 1].",
                details={"confidence": self.confidence},
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        object.__setattr__(self, "premise_ids", tuple(self.premise_ids))

    @property
    def is_premise(self) -> bool:
        """Whether this is a given (a root node with no premises)."""
        return not self.premise_ids

    @property
    def is_grounded(self) -> bool:
        """Whether this node cites at least one piece of evidence."""
        return bool(self.evidence_ids)


@dataclass(frozen=True, slots=True)
class ReasonGraph:
    """An immutable directed acyclic graph of reason nodes.

    Iteration preserves insertion order for deterministic output. Functional
    updates return a new graph.

    Attributes:
        nodes: The reason nodes, keyed by id (read-only).
    """

    nodes: Mapping[ReasonNodeId, ReasonNode] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))

    @classmethod
    def empty(cls) -> ReasonGraph:
        """An empty reason graph."""
        return cls()

    @classmethod
    def of(cls, nodes: Iterable[ReasonNode]) -> ReasonGraph:
        """Build a graph by adding nodes in order (premises must precede).

        Raises:
            InvalidReasonGraphError: On a duplicate id or a premise that has not
                yet been added.
        """
        graph = cls.empty()
        for node in nodes:
            graph = graph.add_node(node)
        return graph

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: ReasonNodeId) -> bool:
        """Whether a node with ``node_id`` exists."""
        return node_id in self.nodes

    def get(self, node_id: ReasonNodeId) -> ReasonNode:
        """Return the node for ``node_id``.

        Raises:
            ReasonNodeNotFoundError: If no such node exists.
        """
        node = self.nodes.get(node_id)
        if node is None:
            raise ReasonNodeNotFoundError(
                f"Reason node {node_id} not found.", details={"node_id": str(node_id)}
            )
        return node

    def add_node(self, node: ReasonNode) -> ReasonGraph:
        """Return a new graph with ``node`` added.

        Enforces the DAG invariant: the id must be new, and every premise the node
        names must already be present (no forward references, hence no cycles).

        Raises:
            InvalidReasonGraphError: On a duplicate id or a missing premise.
        """
        if node.id in self.nodes:
            raise InvalidReasonGraphError(
                "Duplicate reason node id.", details={"id": str(node.id)}
            )
        for premise_id in node.premise_ids:
            if premise_id not in self.nodes:
                raise InvalidReasonGraphError(
                    "Reason node references a premise not yet in the graph.",
                    details={"node": str(node.id), "premise": str(premise_id)},
                )
        return ReasonGraph(nodes=MappingProxyType({**self.nodes, node.id: node}))

    def by_dimension(self, dimension: ReasoningDimension) -> tuple[ReasonNode, ...]:
        """All nodes for a dimension, in insertion order."""
        return tuple(n for n in self.nodes.values() if n.dimension is dimension)

    def roots(self) -> tuple[ReasonNode, ...]:
        """All premise nodes (nodes with no premises of their own)."""
        return tuple(n for n in self.nodes.values() if n.is_premise)

    def premises_of(self, node_id: ReasonNodeId) -> tuple[ReasonNode, ...]:
        """The direct premises of a node, in declared order."""
        node = self.get(node_id)
        return tuple(self.get(pid) for pid in node.premise_ids)

    def ancestors(self, node_id: ReasonNodeId) -> tuple[ReasonNode, ...]:
        """The transitive premise closure of a node (deepest first, deterministic).

        Walks premises breadth-first from the node, returning every ancestor
        exactly once in a stable order. Safe against cycles (which cannot occur by
        construction) via a visited set.
        """
        self.get(node_id)  # validate existence
        seen: set[ReasonNodeId] = set()
        order: list[ReasonNode] = []
        frontier = list(self.get(node_id).premise_ids)
        while frontier:
            current = frontier.pop(0)
            if current in seen:
                continue
            seen.add(current)
            node = self.get(current)
            order.append(node)
            frontier.extend(node.premise_ids)
        return tuple(order)
