"""The Homepage Design Workflow definition — the V1 pipeline expressed as config.

This is **execution**, not architecture. It does not introduce a new engine, abstraction, or
domain layer: it is a single, concrete :class:`~director.domain.workflow.definition.WorkflowDefinition`
— pure data — that the already-built **Director (Phase 2)** interprets at run time. Every capability
the workflow needs (resumability, retry, events, stored reasoning, stored review results, and the
Generate → Critique → Improve → Approve loop) is provided by the Director; this module only
declares the ordered steps and their retry/rollback/approval policies.

The V1 pipeline (frozen scope — Homepage only) is realised in **engine-dependency order**, which is
the only executable order: Research feeds Strategy, Strategy feeds Brand, and so on down to the
Figma model. Each step's ``key`` is the stable dispatch token the engine executor keys on; the
``agent_role`` is the canonical role label carried on events (roles are the fixed platform roster —
the executor decides which engine actually runs from the step key).

Steps and the engine each drives:

1.  ``research``                 → Research (P6)
2.  ``competitor_analysis``      → Competitive Intelligence (P5)
3.  ``business_strategy``        → Business Strategy (P7)  — the business understanding
4.  ``brand_strategy``           → Brand Strategy (P8)
5.  ``customer_psychology``      → Customer Psychology (P9)
6.  ``ux_strategy``              → UX Strategy (P10)
7.  ``information_architecture`` → Information Architecture (P11)
8.  ``wireframe_planning``       → Wireframe Planning (P12)
9.  ``creative_director_review`` → Creative Director (P13)  [gate → rewinds to ux_strategy]
10. ``design_language``          → Design Language (P14)
11. ``component_intelligence``   → Component Intelligence (P15)
12. ``design_system_mapping``    → Design System (P16)
13. ``figma_generation``         → Design Orchestrator (P17) + Figma Design (P18)
14. ``design_critique``          → Creative Director critique of the Figma model (P13)
15. ``self_improvement``         → Figma model regenerated with the critique's required changes
16. ``final_approval``           → Creative Director (P13)  [manual gate → rewinds to self_improvement]

The two gates give the workflow its self-correcting spine: ``creative_director_review`` rewinds to
``ux_strategy`` if the wireframe fails the aesthetic bar; ``final_approval`` rewinds to
``self_improvement`` for another improvement round. The Director caps these loops with its
``max_redesigns`` guard rail.

Pure config: it imports only the Director's definition/value-object types and the core agent role
enum. No engine, no I/O.
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

__all__ = [
    "HOMEPAGE_WORKFLOW_KEY",
    "STEP_BRAND_STRATEGY",
    "STEP_BUSINESS_STRATEGY",
    "STEP_CD_REVIEW",
    "STEP_COMPETITOR_ANALYSIS",
    "STEP_COMPONENT_INTELLIGENCE",
    "STEP_CUSTOMER_PSYCHOLOGY",
    "STEP_DESIGN_CRITIQUE",
    "STEP_DESIGN_LANGUAGE",
    "STEP_DESIGN_SYSTEM_MAPPING",
    "STEP_FIGMA_GENERATION",
    "STEP_FINAL_APPROVAL",
    "STEP_INFORMATION_ARCHITECTURE",
    "STEP_RESEARCH",
    "STEP_SELF_IMPROVEMENT",
    "STEP_UX_STRATEGY",
    "STEP_WIREFRAME_PLANNING",
    "build_homepage_catalog",
    "build_homepage_definition",
]

#: The stable key of the homepage workflow.
HOMEPAGE_WORKFLOW_KEY = "page_homepage"

# --- Step keys (the executor dispatches on these) -------------------------- #
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
STEP_FIGMA_GENERATION = "figma_generation"
STEP_DESIGN_CRITIQUE = "design_critique"
STEP_SELF_IMPROVEMENT = "self_improvement"
STEP_FINAL_APPROVAL = "final_approval"


def _agent(key: str, role: AgentRole, title: str) -> WorkflowStepSpec:
    """A non-gate agent step with the default retry policy."""
    return WorkflowStepSpec(key=key, title=title, agent_role=role, retry=RetryPolicy.default())


def _gate(
    key: str,
    role: AgentRole,
    title: str,
    *,
    rollback_to: str,
    manual: bool = False,
) -> WorkflowStepSpec:
    """A review gate that rewinds to ``rollback_to`` on rejection. Gates are not
    retried — a rejection is a verdict, not a failure."""
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
    """Build the immutable Homepage Design Workflow definition (V1 pipeline)."""
    return WorkflowDefinition(
        key=HOMEPAGE_WORKFLOW_KEY,
        name="Homepage Design Workflow",
        workflow_type=WorkflowType.PAGE,
        page_type=PageType.HOMEPAGE,
        version=1,
        description=(
            "Research → competitor → strategy → brand → psychology → UX → IA → wireframe → "
            "creative-director review → design language → components → design system → Figma "
            "generation → critique → self-improvement → final approval."
        ),
        steps=(
            _agent(STEP_RESEARCH, AgentRole.RESEARCH, "Research"),
            _agent(STEP_COMPETITOR_ANALYSIS, AgentRole.RESEARCH, "Competitor Analysis"),
            _agent(STEP_BUSINESS_STRATEGY, AgentRole.BUSINESS_ANALYST, "Business Strategy"),
            _agent(STEP_BRAND_STRATEGY, AgentRole.BUSINESS_ANALYST, "Brand Strategy"),
            _agent(STEP_CUSTOMER_PSYCHOLOGY, AgentRole.CRO_EXPERT, "Customer Psychology"),
            _agent(STEP_UX_STRATEGY, AgentRole.UX_ARCHITECT, "UX Strategy"),
            _agent(
                STEP_INFORMATION_ARCHITECTURE,
                AgentRole.INFORMATION_ARCHITECT,
                "Information Architecture",
            ),
            _agent(
                STEP_WIREFRAME_PLANNING, AgentRole.INFORMATION_ARCHITECT, "Wireframe Planning"
            ),
            _gate(
                STEP_CD_REVIEW,
                AgentRole.CREATIVE_DIRECTOR,
                "Creative Director Review",
                rollback_to=STEP_UX_STRATEGY,
            ),
            _agent(STEP_DESIGN_LANGUAGE, AgentRole.DESIGN_SYSTEM_ARCHITECT, "Design Language"),
            _agent(
                STEP_COMPONENT_INTELLIGENCE,
                AgentRole.DESIGN_SYSTEM_ARCHITECT,
                "Component Intelligence",
            ),
            _agent(
                STEP_DESIGN_SYSTEM_MAPPING,
                AgentRole.DESIGN_SYSTEM_ARCHITECT,
                "Design System Mapping",
            ),
            _agent(STEP_FIGMA_GENERATION, AgentRole.SENIOR_UI_DESIGNER, "Figma Generation"),
            _agent(STEP_DESIGN_CRITIQUE, AgentRole.CREATIVE_DIRECTOR, "Design Critique"),
            _agent(STEP_SELF_IMPROVEMENT, AgentRole.SENIOR_UI_DESIGNER, "Self Improvement"),
            _gate(
                STEP_FINAL_APPROVAL,
                AgentRole.CREATIVE_DIRECTOR,
                "Final Approval",
                rollback_to=STEP_SELF_IMPROVEMENT,
                manual=True,
            ),
        ),
    )


def build_homepage_catalog() -> WorkflowCatalog:
    """A :class:`WorkflowCatalog` holding just the homepage definition.

    The Director's ``submit_page(page_type=HOMEPAGE)`` resolves the workflow via
    :meth:`WorkflowCatalog.for_page`, so this single-definition catalog is all the Director needs
    to drive the homepage run. The workflow has no composite steps, so no section sub-workflow is
    required.
    """
    return WorkflowCatalog([build_homepage_definition()])
