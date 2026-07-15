"""Grounding gate — Draft Validation.

The token architect *proposes* the design system; this stage is where the domain begins to
*dispose*. It verifies that every citation in the draft — across tokens, component specs, and the
elements they carry — resolves in the consolidated :class:`EvidenceGraph`, failing fast with a
precise error if the architect cited evidence it was never given, so no ungrounded token or
component can enter the specification.

This is the structural realisation of "nothing is chosen at random": a token or component the
architect cannot ground is rejected here, long before it reaches a specification.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from design_system.application.contracts import DesignSystemDraft
from design_system.domain.evidence.evidence import EvidenceGraph
from design_system.domain.shared.ids import DSEvidenceId

__all__ = ["DraftValidator", "UngroundedDesignSystemError"]


class UngroundedDesignSystemError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_design_system"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: DesignSystemDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedDesignSystemError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedDesignSystemError(
                "Design-system draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: DesignSystemDraft) -> Iterable[DSEvidenceId]:
        for token in draft.token_set:
            yield from token.evidence_ids
        for spec in draft.component_specs:
            yield from spec.evidence_ids
