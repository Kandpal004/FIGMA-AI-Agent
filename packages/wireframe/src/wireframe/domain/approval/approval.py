"""The Approval model — the sign-off gates a plan must pass before Figma work begins.

Planning is not done when a section is described; it is done when someone with the authority
to spend design effort has approved it. An :class:`ApprovalRequirement` records the gate a
section must pass (:class:`ApprovalGate`), who signs off (:class:`ApproverRole`), the
criteria that must hold, and which other approvals must land first (``depends_on``). The
:class:`ApprovalPlan` is the set of those requirements — the Approval Graph is its
dependency structure, kept acyclic by the graph primitive.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.ids import ApprovalReqId, SectionId, WFEvidenceId
from wireframe.domain.shared.value_objects import ApprovalGate, ApproverRole

__all__ = ["ApprovalPlan", "ApprovalRequirement", "InvalidApprovalError"]


class InvalidApprovalError(DesignDirectorError):
    """Raised when an approval requirement or plan is constructed with invalid data."""

    code = "invalid_wireframe_approval"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ApprovalRequirement:
    """The gate a section must pass before it is built in Figma.

    Attributes:
        id: Requirement identity.
        target: The section this approval gates.
        gate: The rigor of the gate.
        approver_role: Who signs off.
        criteria: The conditions that must hold to approve.
        depends_on: Approvals that must land before this one (upstream sections).
        evidence_ids: The evidence justifying the gate level.
    """

    id: ApprovalReqId
    target: SectionId
    gate: ApprovalGate
    approver_role: ApproverRole
    criteria: tuple[str, ...] = ()
    depends_on: tuple[ApprovalReqId, ...] = ()
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.id in self.depends_on:
            raise InvalidApprovalError(
                "ApprovalRequirement cannot depend on itself.", details={"id": str(self.id)}
            )
        object.__setattr__(self, "criteria", tuple(c for c in self.criteria if c and c.strip()))
        object.__setattr__(self, "depends_on", tuple(dict.fromkeys(self.depends_on)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class ApprovalPlan:
    """The set of approval requirements a plan derives."""

    requirements: tuple[ApprovalRequirement, ...] = ()

    def __post_init__(self) -> None:
        seen: set[ApprovalReqId] = set()
        for req in self.requirements:
            if req.id in seen:
                raise InvalidApprovalError(
                    "Duplicate approval requirement id.", details={"id": str(req.id)}
                )
            seen.add(req.id)
        object.__setattr__(self, "requirements", tuple(self.requirements))

    @classmethod
    def of(cls, requirements: Iterable[ApprovalRequirement]) -> ApprovalPlan:
        return cls(requirements=tuple(requirements))

    def __len__(self) -> int:
        return len(self.requirements)

    def __iter__(self):
        return iter(self.requirements)

    def ids(self) -> frozenset[ApprovalReqId]:
        return frozenset(r.id for r in self.requirements)

    def by_gate(self, gate: ApprovalGate) -> tuple[ApprovalRequirement, ...]:
        return tuple(r for r in self.requirements if r.gate is gate)

    def for_section(self, section_id: SectionId) -> ApprovalRequirement | None:
        return next((r for r in self.requirements if r.target == section_id), None)

    def roots(self) -> tuple[ApprovalRequirement, ...]:
        """Requirements with no upstream approval dependency."""
        return tuple(r for r in self.requirements if not r.depends_on)

    def evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return tuple(eid for r in self.requirements for eid in r.all_evidence_ids())
