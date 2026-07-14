"""Grounding gate — Draft Validation.

The synthesis port *proposes* the wireframe structure; this stage is where the domain begins
to *dispose*. It verifies that every citation in the draft — across pages, sections, goals,
blocks, components, and per-section approval requirements — resolves in the consolidated
:class:`EvidenceGraph`, failing fast with a precise error if a synthesis adapter cited
evidence it was never given, so no ungrounded decision can enter the plan.

This is the structural realisation of "every recommendation must reference its evidence": a
planning decision that cannot be traced to its evidence is rejected here, long before it
reaches a plan.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from wireframe.application.contracts import WireframeDraft
from wireframe.domain.evidence.evidence import EvidenceGraph
from wireframe.domain.shared.ids import WFEvidenceId

__all__ = ["DraftValidator", "UngroundedWireframeError"]


class UngroundedWireframeError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_wireframe"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: WireframeDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedWireframeError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedWireframeError(
                "Wireframe draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: WireframeDraft) -> Iterable[WFEvidenceId]:
        for page in draft.blueprint.pages:
            yield from page.all_evidence_ids()
