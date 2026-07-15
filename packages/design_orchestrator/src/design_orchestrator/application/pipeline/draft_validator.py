"""Grounding gate — Draft Validation.

The planner *proposes* the ordered sections; this stage is where the domain begins to *dispose*.
It verifies that every citation in the draft — across every section of every page — resolves in
the consolidated :class:`EvidenceGraph`, failing fast with a precise error if the planner cited
evidence it was never given, so no ungrounded ordering or binding can enter the plan.

This is the structural realisation of "no guessing": a choice the planner cannot ground is
rejected here, long before it reaches a plan.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from design_orchestrator.application.contracts import ExecutionDraft
from design_orchestrator.domain.evidence.evidence import EvidenceGraph
from design_orchestrator.domain.shared.ids import DOEvidenceId

__all__ = ["DraftValidator", "UngroundedExecutionPlanError"]


class UngroundedExecutionPlanError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_design_orchestrator_plan"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: ExecutionDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedExecutionPlanError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedExecutionPlanError(
                "Execution draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: ExecutionDraft) -> Iterable[DOEvidenceId]:
        for section in draft.sections:
            yield from section.evidence_ids
