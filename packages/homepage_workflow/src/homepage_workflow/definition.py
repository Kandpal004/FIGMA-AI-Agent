"""The Homepage Design Workflow definition — the V1 per-section pipeline as config.

Execution, not architecture. A single concrete
:class:`~director.domain.workflow.definition.WorkflowDefinition` — pure data — that the already-built
Director (Phase 2) interprets. It declares: input validation, the strategy pipeline (run once), the
generation of the homepage plan backbone, then — **one section at a time** — a generate → score-gated
approve pair for every one of the fourteen homepage sections, and finally a human sign-off.

The section rule is honoured structurally: each ``approve_<section>`` gate rewinds *only* to its own
``generate_<section>`` step, so a rejected section is improved in place and **approved sections are
never regenerated**. The strategy engines run once at the top; the sections are then designed,
critiqued, improved, and approved individually and sequentially.

Pure config: it imports only the Director's definition/value-object types, the core agent role enum,
and the homepage section taxonomy. No engine, no I/O.
"""

from __future__ import annotations

from core.contracts.agent import AgentRole

from director.domain.shared.value_objects import (
    ApprovalPolicy,
    PageType,
    RetryPolicy,
    RollbackPolicy,
    WorkflowType,
)
from director.domain.workflow.catalog import WorkflowCatalog
from director.domain.workflow.definition import WorkflowDefinition, WorkflowStepSpec

from homepage_workflow.section_plan import HOMEPAGE_SECTIONS

__all__ = [
    "HOMEPAGE_WORKFLOW_KEY",
    "STEP_BRAND_STRATEGY",
    "STEP_BUSINESS_STRATEGY",
    "STEP_CD_REVIEW",
    "STEP_COMPETITOR_ANALYSIS",
    "STEP_COMPONENT_INTELLIGENCE",
    "STEP_CUSTOMER_PSYCHOLOGY",
    "STEP_DESIGN_LANGUAGE",
    "STEP_DESIGN_SYSTEM_MAPPING",
    "STEP_FINALIZE",
    "STEP_FINAL_APPROVAL",
    "STEP_GENERATE_HOMEPAGE_PLAN",
    "STEP_INFORMATION_ARCHITECTURE",
    "STEP_RESEARCH",
    "STEP_UX_STRATEGY",
    "STEP_VALIDATE_INPUTS",
    "STEP_WIREFRAME_PLANNING",
    "approve_step_key",
    "build_homepage_catalog",
    "build_homepage_definition",
    "generate_step_key",
    "is_approve_step",
    "is_generate_step",
    "section_of_step",
]

#: The stable key of the homepage workflow.
HOMEPAGE_WORKFLOW_KEY = "page_homepage"

# --- Fixed step keys -------------------------------------------------------- #
STEP_VALIDATE_INPUTS = "validate_inputs"
STEP_RESEARCH = "research"
STEP_COMPETITOR_ANALYSIS = "competitor_analysis"
STEP_BUSINESS_STRATEGY = "business_strategy"
STEP_BRAND_STRATEGY = "brand_strategy"
STEP_CUSTOMER_PSYCHOLOGY = "customer_psychology"
STEP_UX_STRATEGY = "ux_strategy"
STEP_INFORMATION_ARCHITECTURE = "information_architecture"
STEP_WIREFRAME_PLANNING = "wireframe_planning"
STEP_CD_REVIEW = "creative_director_review"
STEP_DESIGN_LANGUAGE = "design_language"
STEP_COMPONENT_INTELLIGENCE = "component_intelligence"
STEP_DESIGN_SYSTEM_MAPPING = "design_system_mapping"
STEP_GENERATE_HOMEPAGE_PLAN = "generate_homepage_plan"
STEP_FINALIZE = "finalize_homepage"
STEP_FINAL_APPROVAL = "final_approval"

# --- Per-section step keys -------------------------------------------------- #
_GENERATE_PREFIX = "generate_section__"
_APPROVE_PREFIX = "approve_section__"


def generate_step_key(section_key: str) -> str:
    """The key of the generate step for a section."""
    return f"{_GENERATE_PREFIX}{section_key}"


def approve_step_key(section_key: str) -> str:
    """The key of the approve gate for a section."""
    return f"{_APPROVE_PREFIX}{section_key}"


def is_generate_step(step_key: str) -> bool:
    return step_key.startswith(_GENERATE_PREFIX)


def is_approve_step(step_key: str) -> bool:
    return step_key.startswith(_APPROVE_PREFIX)


def section_of_step(step_key: str) -> str:
    """The section key a generate/approve step belongs to."""
    if step_key.startswith(_GENERATE_PREFIX):
        return step_key[len(_GENERATE_PREFIX):]
    if step_key.startswith(_APPROVE_PREFIX):
        return step_key[len(_APPROVE_PREFIX):]
    raise ValueError(f"{step_key!r} is not a section step.")


# --- Step builders ---------------------------------------------------------- #
def _agent(key: str, role: AgentRole, title: str) -> WorkflowStepSpec:
    return WorkflowStepSpec(key=key, title=title, agent_role=role, retry=RetryPolicy.default())


def _gate(
    key: str, role: AgentRole, title: str, *, rollback_to: str, manual: bool = False
) -> WorkflowStepSpec:
    return WorkflowStepSpec(
        key=key,
        title=title,
        agent_role=role,
        is_gate=True,
        approval=ApprovalPolicy.manual(1) if manual else ApprovalPolicy.automatic(),
        retry=RetryPolicy.none(),
        rollback=RollbackPolicy.to_target(rollback_to),
    )


def build_homepage_definition() -> WorkflowDefinition:
    """Build the immutable Homepage Design Workflow definition (per-section V1 pipeline)."""
    steps: list[WorkflowStepSpec] = [
        _agent(STEP_VALIDATE_INPUTS, AgentRole.QA, "Validate Inputs"),
        _agent(STEP_RESEARCH, AgentRole.RESEARCH, "Research"),
        _agent(STEP_COMPETITOR_ANALYSIS, AgentRole.RESEARCH, "Competitor Intelligence"),
        _agent(STEP_BUSINESS_STRATEGY, AgentRole.BUSINESS_ANALYST, "Business Strategy"),
        _agent(STEP_BRAND_STRATEGY, AgentRole.BUSINESS_ANALYST, "Brand Strategy"),
        _agent(STEP_CUSTOMER_PSYCHOLOGY, AgentRole.CRO_EXPERT, "Customer Psychology"),
        _agent(STEP_UX_STRATEGY, AgentRole.UX_ARCHITECT, "UX Strategy"),
        _agent(STEP_INFORMATION_ARCHITECTURE, AgentRole.INFORMATION_ARCHITECT,
               "Information Architecture"),
        _agent(STEP_WIREFRAME_PLANNING, AgentRole.INFORMATION_ARCHITECT, "Wireframe Planning"),
        _gate(STEP_CD_REVIEW, AgentRole.CREATIVE_DIRECTOR, "Creative Director Review",
              rollback_to=STEP_UX_STRATEGY),
        _agent(STEP_DESIGN_LANGUAGE, AgentRole.DESIGN_SYSTEM_ARCHITECT, "Design Language"),
        _agent(STEP_COMPONENT_INTELLIGENCE, AgentRole.DESIGN_SYSTEM_ARCHITECT,
               "Component Intelligence"),
        _agent(STEP_DESIGN_SYSTEM_MAPPING, AgentRole.DESIGN_SYSTEM_ARCHITECT,
               "Design System Mapping"),
        _agent(STEP_GENERATE_HOMEPAGE_PLAN, AgentRole.SENIOR_UI_DESIGNER, "Generate Homepage Plan"),
    ]

    # One section at a time: generate → score-gated approve (rewinds only to its own generate).
    for spec in HOMEPAGE_SECTIONS:
        gen = generate_step_key(spec.key)
        steps.append(_agent(gen, AgentRole.SENIOR_UI_DESIGNER, f"Generate — {spec.title}"))
        steps.append(_gate(
            approve_step_key(spec.key), AgentRole.CREATIVE_DIRECTOR, f"Approve — {spec.title}",
            rollback_to=gen,
        ))

    steps.append(_agent(STEP_FINALIZE, AgentRole.SENIOR_UI_DESIGNER, "Finalize Homepage Plan"))
    steps.append(_gate(STEP_FINAL_APPROVAL, AgentRole.CREATIVE_DIRECTOR, "Final Approval",
                       rollback_to=STEP_FINALIZE, manual=True))

    return WorkflowDefinition(
        key=HOMEPAGE_WORKFLOW_KEY,
        name="Homepage Design Workflow",
        workflow_type=WorkflowType.PAGE,
        page_type=PageType.HOMEPAGE,
        version=2,
        description=(
            "Validate → research → competitor → strategy → brand → psychology → UX → IA → "
            "wireframe → creative-director review → design language → components → design system → "
            "homepage plan → per-section generate/approve (×14) → finalize → final approval."
        ),
        steps=tuple(steps),
    )


def build_homepage_catalog() -> WorkflowCatalog:
    """A :class:`WorkflowCatalog` holding just the homepage definition."""
    return WorkflowCatalog([build_homepage_definition()])
