"""The Component Planning model — the components a section requires.

A :class:`ComponentRequirement` states that a section needs a planning-level component
(:class:`ComponentKind`), whether it is required or optional, why, what data it consumes
(:class:`DataContractIntent` — an *abstract* shape, never a UI binding), and which other
components it composes over. This answers *what components a page needs* — it never decides
how a component renders. Component requirements are the nodes of the Component Graph.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.ids import ComponentReqId, WFEvidenceId
from wireframe.domain.shared.value_objects import ComponentKind, DataKind, RequirementLevel

__all__ = ["ComponentRequirement", "DataContractIntent", "InvalidComponentError"]


class InvalidComponentError(DesignDirectorError):
    """Raised when a component requirement is constructed with invalid data."""

    code = "invalid_wireframe_component"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DataContractIntent:
    """The abstract shape of the data a component consumes.

    This describes the *need* — which fields, and whether one or many — so downstream design
    and development know what data to wire, without binding to any schema, API, or UI.

    Attributes:
        fields: The abstract field names the component needs.
        cardinality: "one" for a single record, "many" for a collection.
        data_kind: The kind of data the contract is over, if any.
    """

    fields: tuple[str, ...] = ()
    cardinality: str = "one"
    data_kind: DataKind | None = None

    def __post_init__(self) -> None:
        if self.cardinality not in ("one", "many"):
            raise InvalidComponentError(
                "DataContractIntent.cardinality must be 'one' or 'many'.",
                details={"cardinality": self.cardinality},
            )
        object.__setattr__(self, "fields", tuple(dict.fromkeys(self.fields)))


@dataclass(frozen=True, slots=True)
class ComponentRequirement:
    """A component a section requires (or may optionally carry).

    Attributes:
        id: Requirement identity.
        component: The planning-level component kind.
        requirement: Whether it is required or optional.
        rationale: Why the section needs it (grounded in evidence).
        data_contract: The abstract data the component consumes, if any.
        depends_on: Components this one composes over.
        evidence_ids: The evidence grounding the requirement.
    """

    id: ComponentReqId
    component: ComponentKind
    requirement: RequirementLevel
    rationale: str = ""
    data_contract: DataContractIntent | None = None
    depends_on: tuple[ComponentKind, ...] = ()
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "depends_on", tuple(dict.fromkeys(self.depends_on)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def is_required(self) -> bool:
        return self.requirement is RequirementLevel.REQUIRED

    def all_evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return self.evidence_ids
