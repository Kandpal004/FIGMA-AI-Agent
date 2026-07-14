"""Flows — the ordered, branchable step sequences a user follows.

A :class:`Flow` is a typed (:class:`FlowKind`) sequence of :class:`FlowStep` s with
``PRECEDES`` transitions between them — the User Flow and the Task Flow. Steps are ordered
and the transitions are validated to reference existing steps and to form no cycle (a flow
progresses; it does not loop back into itself). Cited.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import FlowKind, PageKind

__all__ = ["Flow", "FlowSet", "FlowStep", "FlowTransition", "InvalidFlowError"]


class InvalidFlowError(DesignDirectorError):
    """Raised when a flow is constructed with invalid data (dangling/looping transition)."""

    code = "invalid_ux_flow"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FlowStep:
    """One step in a flow.

    Attributes:
        order: The 1-based position of the step.
        action: What the user does at this step.
        page: The page the step happens on, if any.
        is_decision_point: Whether the step is a branch/decision point.
        evidence_ids: The evidence supporting it.
    """

    order: int
    action: str
    page: PageKind | None = None
    is_decision_point: bool = False
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.order < 1:
            raise InvalidFlowError("FlowStep.order must be >= 1.")
        if not self.action or not self.action.strip():
            raise InvalidFlowError("FlowStep.action must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class FlowTransition:
    """A transition from one flow step to another (``from_order`` PRECEDES ``to_order``).

    Attributes:
        from_order: The step the transition leaves.
        to_order: The step the transition enters.
        condition: The condition under which the transition fires.
    """

    from_order: int
    to_order: int
    condition: str = ""


@dataclass(frozen=True, slots=True)
class Flow:
    """A typed, ordered, cited flow."""

    kind: FlowKind
    steps: tuple[FlowStep, ...] = ()
    transitions: tuple[FlowTransition, ...] = ()

    def __post_init__(self) -> None:
        steps = tuple(sorted(self.steps, key=lambda s: s.order))
        orders = [s.order for s in steps]
        if len(set(orders)) != len(orders):
            raise InvalidFlowError("Flow has duplicate step orders.", details={"orders": orders})
        order_set = set(orders)
        transitions = tuple(self.transitions)
        for t in transitions:
            if t.from_order not in order_set or t.to_order not in order_set:
                raise InvalidFlowError(
                    "Flow transition references a step not in the flow.",
                    details={"from": t.from_order, "to": t.to_order},
                )
            if t.to_order <= t.from_order:
                raise InvalidFlowError(
                    "Flow transitions must move forward (a flow does not loop back).",
                    details={"from": t.from_order, "to": t.to_order},
                )
        object.__setattr__(self, "steps", steps)
        object.__setattr__(self, "transitions", transitions)

    @classmethod
    def of(
        cls,
        kind: FlowKind,
        steps: Iterable[FlowStep],
        transitions: Iterable[FlowTransition] = (),
    ) -> Flow:
        return cls(kind=kind, steps=tuple(steps), transitions=tuple(transitions))

    def __len__(self) -> int:
        return len(self.steps)

    def __iter__(self):
        return iter(self.steps)

    def decision_points(self) -> tuple[FlowStep, ...]:
        return tuple(s for s in self.steps if s.is_decision_point)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for s in self.steps for eid in s.evidence_ids)


@dataclass(frozen=True, slots=True)
class FlowSet:
    """An immutable set of flows."""

    flows: tuple[Flow, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "flows", tuple(self.flows))

    @classmethod
    def of(cls, flows: Iterable[Flow]) -> FlowSet:
        return cls(flows=tuple(flows))

    def __len__(self) -> int:
        return len(self.flows)

    def __iter__(self):
        return iter(self.flows)

    def by_kind(self, kind: FlowKind) -> tuple[Flow, ...]:
        return tuple(f for f in self.flows if f.kind is kind)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for f in self.flows for eid in f.evidence_ids())
