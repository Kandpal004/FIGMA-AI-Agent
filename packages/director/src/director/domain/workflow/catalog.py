"""The workflow catalog — the concrete, canonical workflow definitions as config.

This module assembles the platform's actual workflow *plans* (Principle P10:
plans are configuration, not imperative code) and exposes them through a
:class:`WorkflowCatalog` that the Workflow Engine queries by page type or key.

It realises the approved **two-tier** model:

* :data:`SECTION_DESIGN` — the canonical inner design pipeline for a single
  section: research → strategy → UX → wireframe → wireframe-review (gate) → UI →
  UI-review (gate) → design-system / accessibility / performance validation
  (gates) → creative-director gate (manual). This mirrors the Phase 1 pipeline,
  now expressed as data and reused as the inner workflow of every page.
* One **page** definition per :class:`~director.domain.shared.value_objects.PageType`,
  whose composite steps each spawn a section run of :data:`SECTION_DESIGN`.

The catalog validates cross-references at construction: every composite step's
``spawns`` key must resolve to a definition it holds. This is where the
``spawns`` reference introduced in the definition module is checked.

The canonical catalog is obtained via :meth:`WorkflowCatalog.default`, but the
class takes its definitions by injection, so tests and future per-tenant
configurations can supply their own without touching this module.

Testing considerations
----------------------
* :meth:`WorkflowCatalog.default` builds without error (all cross-references
  resolve) and every definition passes its own validation.
* :meth:`for_page` returns the page workflow for each :class:`PageType`; ``get``
  resolves by key (latest version when unspecified) and raises
  :class:`WorkflowNotFoundError` otherwise.
* Constructing a catalog whose composite step spawns an unknown definition
  raises :class:`InvalidWorkflowDefinitionError`.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.contracts.agent import AgentRole
from core.errors import DesignDirectorError

from director.domain.shared.value_objects import (
    ApprovalPolicy,
    PageType,
    RetryPolicy,
    RollbackPolicy,
    WorkflowType,
)
from director.domain.workflow.definition import (
    InvalidWorkflowDefinitionError,
    StepKind,
    WorkflowDefinition,
    WorkflowStepSpec,
)

__all__ = [
    "SECTION_DESIGN",
    "WorkflowCatalog",
    "WorkflowNotFoundError",
    "build_default_catalog",
]

#: Key of the canonical section-design workflow, referenced by page workflows.
SECTION_DESIGN_KEY = "section_design"


class WorkflowNotFoundError(DesignDirectorError):
    """Raised when a workflow is requested by a key/page the catalog lacks."""

    code = "workflow_not_found"
    http_status = 404


# --------------------------------------------------------------------------- #
# The canonical section-design pipeline (data)
# --------------------------------------------------------------------------- #
def _agent_step(key: str, role: AgentRole, title: str) -> WorkflowStepSpec:
    """A non-gate agent step with the default retry policy."""
    return WorkflowStepSpec(
        key=key, title=title, agent_role=role, retry=RetryPolicy.default()
    )


def _gate_step(
    key: str,
    role: AgentRole,
    title: str,
    *,
    rollback_to: str,
    manual: bool = False,
) -> WorkflowStepSpec:
    """An automatic or manual review gate that rewinds to ``rollback_to`` on
    rejection. Gates are not retried (a rejection is a verdict, not a failure)."""
    return WorkflowStepSpec(
        key=key,
        title=title,
        agent_role=role,
        is_gate=True,
        approval=ApprovalPolicy.manual(1) if manual else ApprovalPolicy.automatic(),
        retry=RetryPolicy.none(),
        rollback=RollbackPolicy.to_target(rollback_to),
    )


#: The canonical inner design pipeline for one section.
SECTION_DESIGN: WorkflowDefinition = WorkflowDefinition(
    key=SECTION_DESIGN_KEY,
    name="Section Design Pipeline",
    workflow_type=WorkflowType.SECTION,
    version=1,
    description="Research → strategy → UX → UI → validations → creative-director gate.",
    steps=(
        _agent_step("research", AgentRole.RESEARCH, "Research"),
        _agent_step("strategy", AgentRole.BUSINESS_ANALYST, "Business Strategy"),
        _agent_step("ux", AgentRole.UX_ARCHITECT, "UX Architecture"),
        _agent_step("wireframe", AgentRole.INFORMATION_ARCHITECT, "Wireframe"),
        _gate_step(
            "wireframe_review", AgentRole.REVIEWER, "Wireframe Review", rollback_to="ux"
        ),
        _agent_step("ui", AgentRole.SENIOR_UI_DESIGNER, "UI Design"),
        _gate_step("ui_review", AgentRole.REVIEWER, "UI Review", rollback_to="ui"),
        _gate_step(
            "design_system_validation",
            AgentRole.DESIGN_SYSTEM_ARCHITECT,
            "Design System Validation",
            rollback_to="ui",
        ),
        _gate_step(
            "accessibility_validation",
            AgentRole.ACCESSIBILITY_EXPERT,
            "Accessibility Validation",
            rollback_to="ui",
        ),
        _gate_step(
            "performance_validation",
            AgentRole.PERFORMANCE_EXPERT,
            "Performance Validation",
            rollback_to="ui",
        ),
        _gate_step(
            "creative_director_gate",
            AgentRole.CREATIVE_DIRECTOR,
            "Creative Director Approval",
            rollback_to="ui",
            manual=True,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Page workflows: which sections compose each page (data)
# --------------------------------------------------------------------------- #
#: Default section composition per page type. This is configuration — the set of
#: sections a page is designed from — not visual design. Overridable per tenant
#: in a later phase (Principle P10/P11).
_PAGE_SECTIONS: dict[PageType, tuple[str, ...]] = {
    PageType.HOMEPAGE: ("hero", "value_props", "featured_collection", "social_proof", "footer"),
    PageType.COLLECTION: ("hero", "filters", "product_grid", "pagination", "footer"),
    PageType.PRODUCT: ("gallery", "buy_box", "details", "related_products", "reviews", "footer"),
    PageType.CART: ("line_items", "order_summary", "upsells", "footer"),
    PageType.CHECKOUT: ("contact", "shipping", "payment", "review", "confirmation"),
    PageType.LANDING: ("hero", "benefits", "social_proof", "call_to_action", "footer"),
    PageType.BLOG: ("header", "article_body", "author", "related_posts", "footer"),
    PageType.CUSTOM: ("hero", "content", "footer"),
}


def _page_workflow(page_type: PageType) -> WorkflowDefinition:
    """Build the page-level workflow for ``page_type`` — one composite step per
    section, each spawning the section-design pipeline."""
    steps = tuple(
        WorkflowStepSpec(
            key=section_key,
            title=section_key.replace("_", " ").title(),
            kind=StepKind.COMPOSITE,
            spawns=SECTION_DESIGN_KEY,
        )
        for section_key in _PAGE_SECTIONS[page_type]
    )
    return WorkflowDefinition(
        key=f"page_{page_type.value}",
        name=f"{page_type.value.title()} Page Design",
        workflow_type=WorkflowType.PAGE,
        page_type=page_type,
        version=1,
        steps=steps,
    )


# --------------------------------------------------------------------------- #
# The catalog
# --------------------------------------------------------------------------- #
class WorkflowCatalog:
    """An indexed, self-validating collection of workflow definitions.

    Injected into the Workflow Engine. Not a singleton and holds no mutable
    state after construction — it is an immutable lookup built from the
    definitions it is given.
    """

    def __init__(self, definitions: Iterable[WorkflowDefinition]) -> None:
        by_key: dict[str, WorkflowDefinition] = {}
        by_page: dict[PageType, WorkflowDefinition] = {}
        for definition in definitions:
            # Keep the highest version when duplicates of a key are supplied.
            existing = by_key.get(definition.key)
            if existing is None or definition.version > existing.version:
                by_key[definition.key] = definition
            if definition.workflow_type is WorkflowType.PAGE:
                assert definition.page_type is not None  # guaranteed by definition
                by_page[definition.page_type] = definition

        self._by_key = by_key
        self._by_page = by_page
        self._validate_cross_references()

    def _validate_cross_references(self) -> None:
        """Ensure every composite step spawns a definition the catalog holds."""
        for definition in self._by_key.values():
            for step in definition.steps:
                if step.kind is StepKind.COMPOSITE and step.spawns not in self._by_key:
                    raise InvalidWorkflowDefinitionError(
                        "Composite step spawns an unknown workflow.",
                        details={
                            "workflow": definition.key,
                            "step": step.key,
                            "spawns": step.spawns,
                        },
                    )

    def get(self, key: str, version: int | None = None) -> WorkflowDefinition:
        """Return a definition by key.

        Args:
            key: The workflow key.
            version: A specific version, or ``None`` for the latest held.

        Raises:
            WorkflowNotFoundError: If no matching definition exists.
        """
        definition = self._by_key.get(key)
        if definition is None or (version is not None and definition.version != version):
            raise WorkflowNotFoundError(
                f"No workflow {key!r}"
                + (f" version {version}" if version is not None else "")
                + " in catalog.",
                details={"key": key, "version": version},
            )
        return definition

    def for_page(self, page_type: PageType) -> WorkflowDefinition:
        """Return the page-level workflow for ``page_type``.

        Raises:
            WorkflowNotFoundError: If no page workflow is registered.
        """
        definition = self._by_page.get(page_type)
        if definition is None:
            raise WorkflowNotFoundError(
                f"No page workflow for {page_type.value!r}.",
                details={"page_type": page_type.value},
            )
        return definition

    def section_design(self) -> WorkflowDefinition:
        """Return the canonical section-design workflow."""
        return self.get(SECTION_DESIGN_KEY)

    def all(self) -> tuple[WorkflowDefinition, ...]:
        """All held definitions."""
        return tuple(self._by_key.values())

    @classmethod
    def default(cls) -> WorkflowCatalog:
        """Build the canonical catalog: the section pipeline plus a workflow for
        every page type."""
        return cls(build_default_catalog())


def build_default_catalog() -> tuple[WorkflowDefinition, ...]:
    """Return the canonical set of workflow definitions (section + all pages)."""
    return (SECTION_DESIGN, *(_page_workflow(pt) for pt in PageType))
