"""Stage — Review Planning.

Schedules the ordered :class:`ReviewCheckpoint` s that gate the plan before Figma generation. The
gates are fixed and deterministic — tokens approved, layout approved, accessibility approved,
performance approved, and the final pre-generation sign-off — each pinned to the execution stage
it audits and grounded in the Creative Director's evidence (falling back to any available
evidence so every gate is cited). The pre-generation gate is always last, so nothing reaches
generation ungated.
"""

from __future__ import annotations

from design_orchestrator.domain.evidence.evidence import Citation, DOEvidence, EvidenceGraph
from design_orchestrator.domain.review.review_plan import ReviewCheckpoint, ReviewPlan
from design_orchestrator.domain.shared.ids import ReviewCheckpointId
from design_orchestrator.domain.shared.value_objects import (
    ExecutionStepKind,
    ProvenanceKind,
    ReviewGateKind,
)

__all__ = ["ReviewPlanner"]

# The fixed gate sequence: (gate, stage it audits, statement, pass criteria).
_GATES: tuple[tuple[ReviewGateKind, ExecutionStepKind, str, tuple[str, ...]], ...] = (
    (
        ReviewGateKind.TOKENS_APPROVED,
        ExecutionStepKind.SETUP_TOKENS,
        "Confirm the token setup matches the approved Design System.",
        ("All bindings resolve to Design System tokens.", "No hard-coded values."),
    ),
    (
        ReviewGateKind.LAYOUT_APPROVED,
        ExecutionStepKind.BUILD_PAGE,
        "Confirm page and section ordering matches the wireframe intent.",
        ("Section order is total per page.", "Above-the-fold priority respected."),
    ),
    (
        ReviewGateKind.ACCESSIBILITY_APPROVED,
        ExecutionStepKind.APPLY_ACCESSIBILITY,
        "Confirm every section meets its accessibility directive.",
        ("WCAG AA contrast.", "Keyboard operable with visible focus."),
    ),
    (
        ReviewGateKind.PERFORMANCE_APPROVED,
        ExecutionStepKind.APPLY_RESPONSIVE,
        "Confirm the performance budget across sections.",
        ("Below-the-fold sections lazy-load.", "LCP section is prioritised."),
    ),
    (
        ReviewGateKind.PRE_GENERATION,
        ExecutionStepKind.REVIEW_GATE,
        "Final sign-off before Figma generation.",
        ("All prior gates passed.", "Plan is production-ready."),
    ),
)


class ReviewPlanner:
    """Schedules the fixed, ordered review gates."""

    def build(self, evidence: EvidenceGraph) -> ReviewPlan:
        cite = self._citation(evidence)
        checkpoints = tuple(
            ReviewCheckpoint(
                id=ReviewCheckpointId.new(),
                gate=gate,
                after_step=after,
                statement=statement,
                pass_criteria=criteria,
                citations=cite,
            )
            for gate, after, statement, criteria in _GATES
        )
        return ReviewPlan(checkpoints)

    @staticmethod
    def _citation(evidence: EvidenceGraph) -> tuple[Citation, ...]:
        preferred: list[DOEvidence] = list(
            evidence.by_provenance(ProvenanceKind.CREATIVE_DIRECTOR)
        )
        pool = preferred or list(evidence)
        if not pool:
            return ()
        return (Citation(evidence_id=pool[0].id, relevance="grounds this review gate"),)
