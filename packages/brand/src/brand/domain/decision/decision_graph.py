"""The Brand Decision Graph — the traversable, auditable structure of the brand.

Nodes are :class:`BrandDecision` s; edges are typed :class:`BrandDecisionEdge` s
(``DERIVES_FROM``, ``EXPRESSES``, ``SUPPORTS``, ``ENABLES``, ``CONSTRAINS``,
``CONFLICTS_WITH``). The graph validates that every edge's endpoints exist and that
``DERIVES_FROM`` forms no cycle — a decision cannot ultimately derive from itself.
``EXPRESSES`` links a creative decision to the identity trait it gives form to;
``CONFLICTS_WITH`` may be mutual (a tension to resolve, not a defect).

This is the structure the facade walks to *explain* any brand decision: its full
derivation back to evidence, and what identity it expresses.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from brand.domain.decision.decision import BrandDecision
from brand.domain.shared.ids import (
    BrandDecisionEdgeId,
    BrandDecisionId,
    BrandEvidenceId,
)
from brand.domain.shared.value_objects import BrandDecisionType, DecisionRelation

__all__ = [
    "BrandDecisionEdge",
    "BrandDecisionGraph",
    "DecisionNotFoundError",
    "InvalidDecisionGraphError",
]


class InvalidDecisionGraphError(DesignDirectorError):
    """Raised when the brand decision graph is structurally invalid (dangling/cycle)."""

    code = "invalid_brand_decision_graph"
    http_status = 422


class DecisionNotFoundError(DesignDirectorError):
    """Raised when a decision is requested by an id absent from the graph."""

    code = "brand_decision_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class BrandDecisionEdge:
    """A typed, directed edge between two brand decisions.

    Attributes:
        id: Edge identity.
        source: The decision the edge starts at.
        target: The decision the edge points to.
        relation: The relation the edge expresses.
        evidence_ids: Optional evidence supporting the relationship itself.
    """

    id: BrandDecisionEdgeId
    source: BrandDecisionId
    target: BrandDecisionId
    relation: DecisionRelation
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidDecisionGraphError(
                "BrandDecisionEdge cannot connect a decision to itself.",
                details={"decision": str(self.source)},
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandDecisionGraph:
    """An immutable graph of brand decisions and their typed relationships."""

    decisions: Mapping[BrandDecisionId, BrandDecision] = field(
        default_factory=lambda: MappingProxyType({})
    )
    edges: tuple[BrandDecisionEdge, ...] = ()

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
        adjacency: dict[BrandDecisionId, list[BrandDecisionId]] = {
            d: [] for d in self.decisions
        }
        for edge in self.edges:
            if edge.relation is DecisionRelation.DERIVES_FROM:
                adjacency[edge.source].append(edge.target)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.decisions, WHITE)

        def visit(node: BrandDecisionId) -> None:
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
    def empty(cls) -> BrandDecisionGraph:
        return cls()

    @classmethod
    def of(
        cls,
        decisions: Iterable[BrandDecision],
        edges: Iterable[BrandDecisionEdge] = (),
    ) -> BrandDecisionGraph:
        """Build a graph from decisions and edges.

        Raises:
            InvalidDecisionGraphError: On a duplicate id, a dangling edge, or a
                DERIVES_FROM cycle.
        """
        mapping: dict[BrandDecisionId, BrandDecision] = {}
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

    def has(self, decision_id: BrandDecisionId) -> bool:
        return decision_id in self.decisions

    def get(self, decision_id: BrandDecisionId) -> BrandDecision:
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

    def by_type(self, decision_type: BrandDecisionType) -> tuple[BrandDecision, ...]:
        return tuple(d for d in self.decisions.values() if d.type is decision_type)

    def derivation_of(
        self, decision_id: BrandDecisionId
    ) -> tuple[BrandDecision, ...]:
        """The decisions ``decision_id`` derives from, directly (its parents)."""
        self.get(decision_id)
        parents = [
            e.target
            for e in self.edges
            if e.source == decision_id and e.relation is DecisionRelation.DERIVES_FROM
        ]
        return tuple(self.decisions[p] for p in parents)

    def expressed_by(
        self, decision_id: BrandDecisionId
    ) -> tuple[BrandDecision, ...]:
        """The identity decisions ``decision_id`` gives form to (EXPRESSES targets)."""
        self.get(decision_id)
        targets = [
            e.target
            for e in self.edges
            if e.source == decision_id and e.relation is DecisionRelation.EXPRESSES
        ]
        return tuple(self.decisions[t] for t in targets)

    def conflicts(self) -> tuple[BrandDecisionEdge, ...]:
        return tuple(
            e for e in self.edges if e.relation is DecisionRelation.CONFLICTS_WITH
        )

    def roots(self) -> tuple[BrandDecision, ...]:
        """Decisions that derive from nothing else (foundational brand choices)."""
        has_parent = {
            e.source for e in self.edges if e.relation is DecisionRelation.DERIVES_FROM
        }
        return tuple(d for d in self.decisions.values() if d.id not in has_parent)
