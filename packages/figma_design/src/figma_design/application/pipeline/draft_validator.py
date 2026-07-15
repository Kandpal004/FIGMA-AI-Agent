"""Grounding gate — Draft Validation.

The composer *proposes* the file; this stage is where the domain begins to *dispose*. It verifies
that every citation in the draft — across every node of every page and every component set —
resolves in the consolidated :class:`EvidenceGraph`, failing fast with a precise error if the
composer cited evidence it was never given, so no ungrounded element can enter the model.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from figma_design.application.contracts import FigmaDraft
from figma_design.domain.evidence.evidence import EvidenceGraph
from figma_design.domain.shared.ids import FDEvidenceId

__all__ = ["DraftValidator", "UngroundedFigmaModelError"]


class UngroundedFigmaModelError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_figma_design_model"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: FigmaDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedFigmaModelError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedFigmaModelError(
                "Figma draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: FigmaDraft) -> Iterable[FDEvidenceId]:
        for node in draft.nodes:
            yield from node.evidence_ids
        for component_set in draft.component_sets:
            yield from component_set.evidence_ids
