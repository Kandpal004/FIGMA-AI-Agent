"""Stage — Explanation construction.

Assembles the engine's articulated WHY from the language selection: why the chosen language was
selected, why each considered alternative was rejected, and how the language maximises the
business goals. It turns the selection's reasoning into the auditable
:class:`LanguageExplanation` the facade exposes — the deliberate justification a design director
owes for every language decision.
"""

from __future__ import annotations

from design_language.domain.language.selection import LanguageSelection
from design_language.domain.report.explanation import LanguageExplanation

__all__ = ["ExplanationBuilder"]


class ExplanationBuilder:
    """Builds the articulated explanation from the language selection."""

    def build(self, selection: LanguageSelection) -> LanguageExplanation:
        why_rejected = tuple(
            f"{alt.option}: {alt.reason_rejected}" for alt in selection.considered
        )
        return LanguageExplanation(
            why_selected=selection.rationale,
            business_alignment=selection.business_alignment,
            why_rejected=why_rejected,
            evidence_ids=selection.all_evidence_ids(),
        )
