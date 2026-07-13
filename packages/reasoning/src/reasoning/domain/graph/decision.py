"""The Decision Graph — the engine's structured record of strategic choices.

A :class:`DecisionNode` is one choice the strategy makes (e.g. "include a hero
section", "use a high-contrast serif for editorial trust"). It records the option
*chosen*, the options *considered and rejected* (which feed trade-offs and
alternative strategies), the reasons that justify it, its dependencies on other
decisions, and its confidence. A :class:`DecisionGraph` links decisions by their
``depends_on`` edges into a directed acyclic graph.

A decision must be *justified*: it must cite evidence directly (via its chosen
option) or through the reasons it references. A baseless decision cannot be
constructed — the anti-hallucination guarantee, enforced at the node level and
re-checked against the evidence graph by the aggregate.

Acyclicity is guaranteed by construction: a decision may be added only once every
decision it depends on already exists.

Testing considerations
----------------------
* A :class:`DecisionOption` requires a non-empty label and a non-negative score.
* A :class:`DecisionNode` with neither evidence nor reasons is rejected; confidence
  is validated to ``[0, 1]``.
* Adding a node whose dependency is absent, or whose id already exists, raises
  :class:`InvalidDecisionGraphError`; cycles are therefore impossible.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import DecisionNodeId, EvidenceId, ReasonNodeId
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = [
    "DecisionGraph",
    "DecisionNode",
    "DecisionNodeNotFoundError",
    "DecisionOption",
    "InvalidDecisionGraphError",
]


class InvalidDecisionGraphError(DesignDirectorError):
    """Raised when a decision node/option/edge is invalid."""

    code = "invalid_decision_graph"
    http_status = 422


class DecisionNodeNotFoundError(DesignDirectorError):
    """Raised when a decision node is requested by an id absent from the graph."""

    code = "decision_node_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class DecisionOption:
    """A candidate option weighed when making a decision.

    Attributes:
        label: The option's human label.
        evidence_ids: Evidence supporting this option.
        score: The deterministic score assigned to this option (``>= 0``).
        note: Optional annotation.
    """

    label: str
    evidence_ids: tuple[EvidenceId, ...] = ()
    score: float = 0.0
    note: str = ""

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidDecisionGraphError("DecisionOption.label must be non-empty.")
        if self.score < 0:
            raise InvalidDecisionGraphError(
                "DecisionOption.score must be >= 0.", details={"score": self.score}
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class DecisionNode:
    """One strategic choice in the decision graph.

    Attributes:
        id: Node identity.
        dimension: The strategy dimension this decision concerns.
        question: The choice being made.
        chosen: The selected option.
        considered: The options that were considered and rejected.
        reason_ids: The reasons that justify the choice.
        confidence: Confidence in the choice, in ``[0, 1]``.
        depends_on: Other decisions this one depends on.
    """

    id: DecisionNodeId
    dimension: ReasoningDimension
    question: str
    chosen: DecisionOption
    confidence: float
    considered: tuple[DecisionOption, ...] = ()
    reason_ids: tuple[ReasonNodeId, ...] = ()
    depends_on: tuple[DecisionNodeId, ...] = ()

    def __post_init__(self) -> None:
        if not self.question or not self.question.strip():
            raise InvalidDecisionGraphError("DecisionNode.question must be non-empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidDecisionGraphError(
                "DecisionNode.confidence must be within [0, 1].",
                details={"confidence": self.confidence},
            )
        if not self.chosen.evidence_ids and not self.reason_ids:
            raise InvalidDecisionGraphError(
                "A decision must cite evidence or reference a reason (no baseless "
                "decisions).",
                details={"question": self.question},
            )
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "reason_ids", tuple(self.reason_ids))
        object.__setattr__(self, "depends_on", tuple(self.depends_on))

    @property
    def all_options(self) -> tuple[DecisionOption, ...]:
        """The chosen option followed by the rejected ones."""
        return (self.chosen, *self.considered)

    @property
    def evidence_ids(self) -> tuple[EvidenceId, ...]:
        """All evidence referenced across every option of this decision."""
        seen: list[EvidenceId] = []
        for option in self.all_options:
            for eid in option.evidence_ids:
                if eid not in seen:
                    seen.append(eid)
        return tuple(seen)


@dataclass(frozen=True, slots=True)
class DecisionGraph:
    """An immutable directed acyclic graph of decision nodes."""

    nodes: Mapping[DecisionNodeId, DecisionNode] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))

    @classmethod
    def empty(cls) -> DecisionGraph:
        """An empty decision graph."""
        return cls()

    @classmethod
    def of(cls, nodes: Iterable[DecisionNode]) -> DecisionGraph:
        """Build a graph by adding nodes in order (dependencies must precede)."""
        graph = cls.empty()
        for node in nodes:
            graph = graph.add_node(node)
        return graph

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    def has(self, node_id: DecisionNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: DecisionNodeId) -> DecisionNode:
        """Return the node for ``node_id``.

        Raises:
            DecisionNodeNotFoundError: If no such node exists.
        """
        node = self.nodes.get(node_id)
        if node is None:
            raise DecisionNodeNotFoundError(
                f"Decision node {node_id} not found.", details={"node_id": str(node_id)}
            )
        return node

    def add_node(self, node: DecisionNode) -> DecisionGraph:
        """Return a new graph with ``node`` added (enforcing the DAG invariant)."""
        if node.id in self.nodes:
            raise InvalidDecisionGraphError(
                "Duplicate decision node id.", details={"id": str(node.id)}
            )
        for dep in node.depends_on:
            if dep not in self.nodes:
                raise InvalidDecisionGraphError(
                    "Decision node references a dependency not yet in the graph.",
                    details={"node": str(node.id), "depends_on": str(dep)},
                )
        return DecisionGraph(nodes=MappingProxyType({**self.nodes, node.id: node}))

    def by_dimension(self, dimension: ReasoningDimension) -> tuple[DecisionNode, ...]:
        return tuple(n for n in self.nodes.values() if n.dimension is dimension)

    def dependencies_of(self, node_id: DecisionNodeId) -> tuple[DecisionNode, ...]:
        """The direct dependencies of a node."""
        node = self.get(node_id)
        return tuple(self.get(d) for d in node.depends_on)

    def ancestors(self, node_id: DecisionNodeId) -> tuple[DecisionNode, ...]:
        """The transitive dependency closure of a node (deterministic order)."""
        self.get(node_id)
        seen: set[DecisionNodeId] = set()
        order: list[DecisionNode] = []
        frontier = list(self.get(node_id).depends_on)
        while frontier:
            current = frontier.pop(0)
            if current in seen:
                continue
            seen.add(current)
            node = self.get(current)
            order.append(node)
            frontier.extend(node.depends_on)
        return tuple(order)
