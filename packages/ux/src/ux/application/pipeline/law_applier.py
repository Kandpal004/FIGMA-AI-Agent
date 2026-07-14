"""Stage — UX law application.

Applies all eleven UX laws / heuristics to the strategy, producing a
:class:`UXLawApplication` for each with where it applies, its rationale, its enforcement
strength, and its guardrail. Each application cites the most relevant consolidated
evidence (falling back to the strongest available), so the strategy is not just principled
but *grounded* — every heuristic is tied to the evidence that justifies its use here.
Covering all eleven laws is what drives the report's heuristic-validation score.
"""

from __future__ import annotations

from collections.abc import Sequence

from ux.domain.evidence.evidence import EvidenceGraph, UXEvidence
from ux.domain.laws.lens import UXLawApplication, UXLawLens
from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import RuleEnforcement, UXLaw, WCAGLevel

__all__ = ["LawApplier"]

# Static knowledge base: law → (where it applies, rationale, enforcement, keywords, guardrail).
_LAWS: dict[UXLaw, tuple[str, str, RuleEnforcement, tuple[str, ...], str]] = {
    UXLaw.JAKOBS: (
        "navigation and page layout",
        "Users spend most of their time on other sites; match the conventions they already know.",
        RuleEnforcement.SHOULD, ("navigation", "convention", "pattern"),
        "Deviate from convention only when there is a proven, evidence-backed reason.",
    ),
    UXLaw.HICKS: (
        "calls to action and choice points",
        "Reduce the number and complexity of choices to speed the decision.",
        RuleEnforcement.SHOULD, ("choice", "cta", "decision", "option"),
        "Do not hide essential options; simplify, don't strip.",
    ),
    UXLaw.FITTS: (
        "primary action targets",
        "Make important targets large and close to the pointer/thumb to reduce effort.",
        RuleEnforcement.SHOULD, ("cta", "button", "action", "mobile"),
        "Prominence must match true priority, not manipulate.",
    ),
    UXLaw.MILLERS: (
        "information grouping",
        "Chunk information into small groups; do not overload working memory.",
        RuleEnforcement.SHOULD, ("information", "content", "cognitive", "load"),
        "Chunking must aid comprehension, not fragment meaning.",
    ),
    UXLaw.TESLERS: (
        "complexity handling",
        "Inherent complexity cannot be removed; move it away from the user where possible.",
        RuleEnforcement.SHOULD, ("complexity", "form", "checkout"),
        "Never shift complexity onto the user to save build effort.",
    ),
    UXLaw.OCCAMS: (
        "content and flow simplicity",
        "Prefer the simplest solution that meets the goal; remove the non-essential.",
        RuleEnforcement.SHOULD, ("simple", "clarity", "content"),
        "Simplicity must not sacrifice necessary information or trust.",
    ),
    UXLaw.PROGRESSIVE_DISCLOSURE: (
        "product and checkout detail",
        "Reveal detail progressively so the primary path stays clear.",
        RuleEnforcement.SHOULD, ("disclosure", "detail", "reveal", "information"),
        "Never hide information the decision genuinely requires.",
    ),
    UXLaw.GESTALT: (
        "visual grouping and hierarchy",
        "Use proximity, similarity, and continuity so structure is perceived effortlessly.",
        RuleEnforcement.SHOULD, ("hierarchy", "group", "visual", "layout"),
        "Grouping must reflect real relationships, not impose false ones.",
    ),
    UXLaw.NIELSEN_HEURISTICS: (
        "interaction feedback and error handling",
        "Honour the ten usability heuristics — visibility of status, error prevention, recovery.",
        RuleEnforcement.SHOULD, ("feedback", "error", "usability", "status"),
        "Feedback must be honest; error messages must help, not blame.",
    ),
    UXLaw.BAYMARD: (
        "cart and checkout",
        "Apply Baymard's empirical ecommerce checkout and PLP/PDP findings.",
        RuleEnforcement.SHOULD, ("checkout", "cart", "ecommerce", "conversion"),
        "Apply patterns that are proven, not merely popular.",
    ),
    UXLaw.WCAG: (
        "the entire experience",
        "Meet WCAG conformance so the experience is perceivable, operable, and understandable to all.",
        RuleEnforcement.MUST, ("accessibility", "wcag", "contrast", "a11y"),
        "Accessibility is a requirement, never a trade-off.",
    ),
}


class LawApplier:
    """Applies the eleven UX laws, grounded in the consolidated evidence."""

    def apply(self, evidence: EvidenceGraph) -> UXLawLens:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        applications = [
            UXLawApplication(
                law=law,
                where_applies=where,
                rationale=rationale,
                enforcement=enforcement,
                wcag_level=WCAGLevel.AA if law is UXLaw.WCAG else None,
                guardrail=guardrail,
                evidence_ids=self._cite(ranked, keywords),
            )
            for law, (where, rationale, enforcement, keywords, guardrail) in _LAWS.items()
        ]
        return UXLawLens.of(applications)

    @staticmethod
    def _cite(
        ranked: Sequence[UXEvidence], keywords: Sequence[str], limit: int = 1
    ) -> tuple[UXEvidenceId, ...]:
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]
        matched = [
            e
            for e in ranked
            if any(
                k in f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
                for k in kws
            )
        ]
        chosen = matched[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)
