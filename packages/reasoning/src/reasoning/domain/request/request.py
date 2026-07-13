"""The engine's inputs — the request and the assembled reasoning context.

A :class:`ReasoningRequest` is what a caller submits: the user's ask plus the
identifiers and framing the engine needs. The engine then loads the surrounding
facts through its ports (brand, project memory, prior decisions, workflow) and
assembles them, together with the request, into an immutable
:class:`ReasoningContext` — the single value every dimension reasoner reads from.

To respect the ports-and-adapters boundary, the loaded facts are held as
engine-local value objects (:class:`BrandContext`, :class:`ContextFact`,
:class:`PriorDecisionRef`, :class:`WorkflowSnapshot`), *not* Phase-2/3 types. The
infrastructure adapters translate the prior phases' models into these.

Pure domain: standard library, the shared-kernel error base, and shared enums.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from reasoning.domain.shared.value_objects import StrategyStance

__all__ = [
    "BrandContext",
    "ContextFact",
    "InvalidReasoningRequestError",
    "PriorDecisionRef",
    "ReasoningContext",
    "ReasoningRequest",
    "WorkflowSnapshot",
]


class InvalidReasoningRequestError(DesignDirectorError):
    """Raised when a reasoning request is constructed with invalid data."""

    code = "invalid_reasoning_request"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    """What a caller asks the engine to reason about.

    Attributes:
        user_request: The natural-language ask.
        project_id: The owning project (UUID string).
        section_id: The section under design (UUID string).
        page_type: The page kind (e.g. ``"product"``, ``"homepage"``).
        platform: The target platform slug (``"shopify_plus"`` / ``"magento"`` /
            ``"agnostic"``), or ``None``. Held as a string to stay decoupled from
            Phase-3's Platform enum; the adapter maps it.
        goal: A short objective (e.g. "increase add-to-cart").
        stance: The strategic lens to reason under.
        component_type: The component under design, if narrowly scoped.
        contexts: Situational tags (normalized slugs) to focus reasoning.
    """

    user_request: str
    project_id: str
    section_id: str
    page_type: str
    platform: str | None = None
    goal: str = ""
    stance: StrategyStance = StrategyStance.BALANCED
    component_type: str | None = None
    contexts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("user_request", self.user_request),
            ("project_id", self.project_id),
            ("section_id", self.section_id),
            ("page_type", self.page_type),
        ):
            if not value or not value.strip():
                raise InvalidReasoningRequestError(f"ReasoningRequest.{name} must be non-empty.")
        object.__setattr__(self, "contexts", tuple(self.contexts))


@dataclass(frozen=True, slots=True)
class ContextFact:
    """One fact loaded from project memory (a decoupled projection of a Phase-2
    memory record)."""

    kind: str
    statement: str


@dataclass(frozen=True, slots=True)
class BrandContext:
    """The brand facts the strategy must honour.

    Attributes:
        voice: The brand voice, if known.
        values: The brand values.
        notes: Free-text brand notes.
        attributes: Arbitrary brand attributes (read-only).
    """

    voice: str = ""
    values: tuple[str, ...] = ()
    notes: str = ""
    attributes: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))
        if not isinstance(self.attributes, MappingProxyType):
            object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))


@dataclass(frozen=True, slots=True)
class PriorDecisionRef:
    """A prior decision (from the Phase-2 log) that constrains this reasoning.

    Approved prior decisions enter the reason graph as premises, so the strategy is
    consistent with what has already been decided.

    Attributes:
        summary: What was decided.
        kind: The decision kind.
        approved: Whether it was approved (and therefore binding).
        at: When it was made (ISO string), if known.
    """

    summary: str
    kind: str = ""
    approved: bool = False
    at: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    """The workflow state at reasoning time (decoupled from Phase-2 types).

    Attributes:
        run_id: The active run id (UUID string), if any.
        current_step: The current step key, if any.
        status: The run status.
    """

    run_id: str | None = None
    current_step: str | None = None
    status: str = ""


@dataclass(frozen=True, slots=True)
class ReasoningContext:
    """The immutable, assembled context every dimension reasoner reads from.

    Attributes:
        request: The originating request.
        brand: The brand context.
        memory_facts: Facts loaded from project memory.
        prior_decisions: Prior decisions that constrain reasoning.
        workflow: The workflow snapshot, if any.
    """

    request: ReasoningRequest
    brand: BrandContext = field(default_factory=BrandContext)
    memory_facts: tuple[ContextFact, ...] = ()
    prior_decisions: tuple[PriorDecisionRef, ...] = ()
    workflow: WorkflowSnapshot | None = None
    tenant_id: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "memory_facts", tuple(self.memory_facts))
        object.__setattr__(self, "prior_decisions", tuple(self.prior_decisions))

    @property
    def stance(self) -> StrategyStance:
        """The stance to reason under."""
        return self.request.stance

    def approved_decisions(self) -> tuple[PriorDecisionRef, ...]:
        """The prior decisions that are approved (and therefore binding)."""
        return tuple(d for d in self.prior_decisions if d.approved)

    @classmethod
    def build(
        cls,
        request: ReasoningRequest,
        *,
        brand: BrandContext | None = None,
        memory_facts: Iterable[ContextFact] = (),
        prior_decisions: Iterable[PriorDecisionRef] = (),
        workflow: WorkflowSnapshot | None = None,
        tenant_id: object | None = None,
    ) -> ReasoningContext:
        """Ergonomic constructor accepting iterables."""
        return cls(
            request=request,
            brand=brand or BrandContext(),
            memory_facts=tuple(memory_facts),
            prior_decisions=tuple(prior_decisions),
            workflow=workflow,
            tenant_id=tenant_id,
        )
