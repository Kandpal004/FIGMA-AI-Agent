"""The Strategy Graph — the interlock map of the strategy's pillars.

Where the decision graph is fine-grained (every atomic choice), the strategy graph is
the executive map: the eight positioning pillars (goals, customer, positioning, value,
messaging, trust, pricing, retention) and how they inform, reinforce, depend on, or
tension with one another. It is what lets a strategist see the whole board at once.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyComponentId, StrategyEdgeId
from strategy.domain.shared.value_objects import DecisionType, StrategyRelation

__all__ = [
    "InvalidStrategyGraphError",
    "StrategyComponent",
    "StrategyEdge",
    "StrategyGraph",
]


class InvalidStrategyGraphError(DesignDirectorError):
    """Raised when the strategy graph is structurally invalid (a dangling edge)."""

    code = "invalid_strategy_graph"
    http_status = 422


@dataclass(frozen=True, slots=True)
class StrategyComponent:
    """One pillar of the strategy.

    Attributes:
        id: Component identity.
        domain: The strategic domain it represents.
        name: A short name.
        summary: A one-line summary of the pillar's stance.
    """

    id: StrategyComponentId
    domain: DecisionType
    name: str
    summary: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidStrategyGraphError("StrategyComponent.name must be non-empty.")


@dataclass(frozen=True, slots=True)
class StrategyEdge:
    """A typed edge between two strategy components.

    Attributes:
        id: Edge identity.
        source: The component the edge starts at.
        target: The component the edge points to.
        relation: The relation it expresses.
    """

    id: StrategyEdgeId
    source: StrategyComponentId
    target: StrategyComponentId
    relation: StrategyRelation

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise InvalidStrategyGraphError(
                "StrategyEdge cannot connect a component to itself.",
                details={"component": str(self.source)},
            )


@dataclass(frozen=True, slots=True)
class StrategyGraph:
    """An immutable interlock map of strategy components."""

    components: Mapping[StrategyComponentId, StrategyComponent] = field(
        default_factory=lambda: MappingProxyType({})
    )
    edges: tuple[StrategyEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.components, MappingProxyType):
            object.__setattr__(self, "components", MappingProxyType(dict(self.components)))
        object.__setattr__(self, "edges", tuple(self.edges))
        for edge in self.edges:
            if edge.source not in self.components:
                raise InvalidStrategyGraphError(
                    "Edge references a source component not in the graph.",
                    details={"edge": str(edge.id)},
                )
            if edge.target not in self.components:
                raise InvalidStrategyGraphError(
                    "Edge references a target component not in the graph.",
                    details={"edge": str(edge.id)},
                )

    @classmethod
    def empty(cls) -> StrategyGraph:
        return cls()

    @classmethod
    def of(
        cls,
        components: Iterable[StrategyComponent],
        edges: Iterable[StrategyEdge] = (),
    ) -> StrategyGraph:
        """Build a graph from components and edges.

        Raises:
            InvalidStrategyGraphError: On a duplicate id or a dangling edge.
        """
        mapping: dict[StrategyComponentId, StrategyComponent] = {}
        for component in components:
            if component.id in mapping:
                raise InvalidStrategyGraphError(
                    "Duplicate component id in graph.", details={"id": str(component.id)}
                )
            mapping[component.id] = component
        return cls(components=MappingProxyType(mapping), edges=tuple(edges))

    def __len__(self) -> int:
        return len(self.components)

    def __iter__(self):
        return iter(self.components.values())

    def has(self, component_id: StrategyComponentId) -> bool:
        return component_id in self.components

    def by_domain(self, domain: DecisionType) -> tuple[StrategyComponent, ...]:
        return tuple(c for c in self.components.values() if c.domain is domain)

    def tensions(self) -> tuple[StrategyEdge, ...]:
        return tuple(e for e in self.edges if e.relation is StrategyRelation.TENSIONS_WITH)
