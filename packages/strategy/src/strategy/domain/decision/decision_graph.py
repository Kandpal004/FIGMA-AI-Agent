"""The Decision Graph — the traversable, auditable structure of the strategy.

Nodes are :class:`StrategicDecision` s; edges are typed
:class:`DecisionEdge` s (``DERIVES_FROM``, ``SUPPORTS``, ``ENABLES``, ``CONSTRAINS``,
``CONFLICTS_WITH``, ``TRADES_OFF_AGAINST``). The graph validates that every edge's
endpoints exist and that ``DERIVES_FROM`` forms no cycle — a decision cannot
ultimately derive from itself. ``CONFLICTS_WITH`` is allowed to be mutual; it names a
tension to resolve, not a defect.

This is the structure the facade walks to *explain* any decision: its full derivation
back to evidence, and the conflicts it participates in.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from strategy.domain.decision.decision import StrategicDecision
from strategy.domain.shared.ids import (
    DecisionEdgeId,
    StrategicDecisionId,
    StrategyEvidenceId,
)
from strategy.domain.shared.value_objects import DecisionRelation, DecisionType

__all__ = [
    "DecisionEdge",
    "DecisionGraph",
    "DecisionNotFoundError",
    "InvalidDecisionGraphError",
]


class InvalidDecisionGraphError(DesignDirectorError):
    """Raised when the decision graph is structurally invalid (dangling edge/cycle)."""

    code = "invalid_decision_graph"
    http_status = 422


class DecisionNotFoundError(DesignDirectorError):
    """Raised when a decision is requested by an id absent from the graph."""

    code = "strategic_decision_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class DecisionEdge:
    """A typed, directed edge between two strategic decisions.

    Attributes:
        id: Edge identity.
        source: The decision the edge starts at.
        target: The decision the edge points to.
        relation: The relation the edge expresses.
        evidence_ids: Optional evidence supporting the relationship itself.
    """

    id: DecisionEdgeId
    source: StrategicDecisionId
    target: StrategicDecisionId
    relation: DecisionRelation
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidDecisionGraphError(
                "DecisionEdge cannot connect a decision to itself.",
                details={"decision": str(self.source)},
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class DecisionGraph:
    """An immutable graph of strategic decisions and their typed relationships."""

    decisions: Mapping[StrategicDecisionId, StrategicDecision] = field(
        default_factory=lambda: MappingProxyType({})
    )
    edges: tuple[DecisionEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.decisions, MappingProxyType):
            object.__setattr__(self, "decisions", MappingProxyType(dict(self.decisions)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.decisions:
                raise InvalidDecisionGraphError(
                    "Edge references a source decision not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.decisions:
                raise InvalidDecisionGraphError(
                    "Edge references a target decision not in the graph.",
                    details={"edge": str(edge.id)},
                )
        self._assert_derivation_acyclic()

    def _assert_derivation_acyclic(self) -> None:
        adjacency: dict[StrategicDecisionId, list[StrategicDecisionId]] = {
            d: [] for d in self.decisions
        }
        for edge in self.edges:
            if edge.relation is DecisionRelation.DERIVES_FROM:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.decisions, WHITE)

        def visit(node: StrategicDecisionId) -> None:
            colour[node] = GREY
            for nxt in adjacency[node]:
                if colour[nxt] == GREY:
                    raise InvalidDecisionGraphError(
                        "DERIVES_FROM relations form a cycle.",
                        details={"decision": str(nxt)},
                    )
                if colour[nxt] == WHITE:
                    visit(nxt)
            colour[node] = BLACK

        for node in self.decisions:
            if colour[node] == WHITE:
                visit(node)

    @classmethod
    def empty(cls) -> DecisionGraph:
        return cls()

    @classmethod
    def of(
        cls,
        decisions: Iterable[StrategicDecision],
        edges: Iterable[DecisionEdge] = (),
    ) -> DecisionGraph:
        """Build a graph from decisions and edges.

        Raises:
            InvalidDecisionGraphError: On a duplicate id, a dangling edge, or a
                DERIVES_FROM cycle.
        """
        mapping: dict[StrategicDecisionId, StrategicDecision] = {}
        for decision in decisions:
            if decision.id in mapping:
                raise InvalidDecisionGraphError(
                    "Duplicate decision id in graph.", details={"id": str(decision.id)}
                )
            mapping[decision.id] = decision
        return cls(decisions=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.decisions)

    def __iter__(self):
        return iter(self.decisions.values())

    def has(self, decision_id: StrategicDecisionId) -> bool:
        return decision_id in self.decisions

    def get(self, decision_id: StrategicDecisionId) -> StrategicDecision:
        """Return the decision for ``decision_id``.

        Raises:
            DecisionNotFoundError: If no such decision exists.
        """
        decision = self.decisions.get(decision_id)
        if decision is None:
            raise DecisionNotFoundError(
                f"Decision {decision_id} not found.",
                details={"decision_id": str(decision_id)},
            )
        return decision

    def by_type(self, decision_type: DecisionType) -> tuple[StrategicDecision, ...]:
        return tuple(d for d in self.decisions.values() if d.type is decision_type)

    def edges_from(self, decision_id: StrategicDecisionId) -> tuple[DecisionEdge, ...]:
        return tuple(e for e in self.edges if e.source == decision_id)

    def derivation_of(
        self, decision_id: StrategicDecisionId
    ) -> tuple[StrategicDecision, ...]:
        """The decisions ``decision_id`` derives from, directly (its parents)."""
        self.get(decision_id)
        parents = [
            e.target
            for e in self.edges
            if e.source == decision_id and e.relation is DecisionRelation.DERIVES_FROM
        ]
        return tuple(self.decisions[p] for p in parents)

    def conflicts(self) -> tuple[DecisionEdge, ...]:
        """All edges expressing a strategic tension."""
        return tuple(
            e for e in self.edges if e.relation is DecisionRelation.CONFLICTS_WITH
        )

    def roots(self) -> tuple[StrategicDecision, ...]:
        """Decisions that derive from nothing else (foundational choices)."""
        has_parent = {
            e.source
            for e in self.edges
            if e.relation is DecisionRelation.DERIVES_FROM
        }
        return tuple(d for d in self.decisions.values() if d.id not in has_parent)
