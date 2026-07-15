"""Stage — Constraint Building.

Derives the rules every future UI must obey from the draft and the brief. Two are always emitted
and always blocking — ``TOKEN_ONLY`` and ``NO_HARDCODED`` — the non-negotiable floor of any
design system. The rest are derived from what the system actually contains:

* ``SPACING_GRID`` — keyed to the spacing scale's grid unit.
* ``TYPE_SCALE`` — keyed to the typography ratio.
* ``CONTRAST_MIN`` — the minimum contrast across the component accessibility specs.
* ``ACCESSIBILITY`` and ``PERFORMANCE`` — always present (recommended-to-blocking).
* ``THEME_PARITY`` — blocking when a dark theme is present.
* ``RTL_MIRROR`` — blocking when the localization contract supports RTL.

Each constraint is grounded by citing the most relevant available evidence, so the assembled
specification's provenance invariant holds.
"""

from __future__ import annotations

from design_system.application.contracts import DesignSystemDraft
from design_system.domain.evidence.evidence import Citation, DSEvidence, EvidenceGraph
from design_system.domain.constraint.constraint import Constraint, ConstraintSet
from design_system.domain.shared.ids import ConstraintId
from design_system.domain.shared.value_objects import (
    ConstraintKind,
    EnforcementLevel,
    ProvenanceKind,
)

__all__ = ["ConstraintBuilder"]

_B = EnforcementLevel.BLOCKING
_R = EnforcementLevel.RECOMMENDED


class ConstraintBuilder:
    """Derives the design system's enforced constraints from the draft."""

    def build(self, draft: DesignSystemDraft, evidence: EvidenceGraph) -> ConstraintSet:
        cite = self._citation_picker(evidence)
        constraints: list[Constraint] = [
            self._c(
                ConstraintKind.TOKEN_ONLY,
                _B,
                "Every visual value must come from a design token; no literal values in UI.",
                "Tokens are the single source of truth; literals fork the system.",
                cite(ProvenanceKind.KNOWLEDGE, ProvenanceKind.DESIGN_LANGUAGE),
            ),
            self._c(
                ConstraintKind.NO_HARDCODED,
                _B,
                "No hard-coded colours, sizes, spacings, or type values anywhere.",
                "Hard-coded values break theming, RTL, and responsive behaviour.",
                cite(ProvenanceKind.KNOWLEDGE, ProvenanceKind.CREATIVE_DIRECTOR),
            ),
            self._c(
                ConstraintKind.SPACING_GRID,
                _B,
                f"All spacing must be a multiple of the {draft.spacing.base_px:g}px grid unit.",
                "A single spacing grid keeps rhythm consistent across every page.",
                cite(ProvenanceKind.WIREFRAME, ProvenanceKind.DESIGN_LANGUAGE),
                {"grid_px": f"{draft.spacing.base_px:g}"},
            ),
            self._c(
                ConstraintKind.TYPE_SCALE,
                _B,
                f"All type sizes must come from the {draft.typography.ratio.value:g} modular "
                "scale.",
                "A modular type scale keeps hierarchy legible and predictable.",
                cite(ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.BRAND_STRATEGY),
                {"ratio": f"{draft.typography.ratio.value:g}"},
            ),
            self._c(
                ConstraintKind.CONTRAST_MIN,
                _B,
                f"Text must meet at least {self._min_contrast(draft):g}:1 contrast (WCAG AA).",
                "Sufficient contrast is a legal and usability floor.",
                cite(ProvenanceKind.UX_STRATEGY, ProvenanceKind.KNOWLEDGE),
                {"min_contrast": f"{self._min_contrast(draft):g}"},
            ),
            self._c(
                ConstraintKind.ACCESSIBILITY,
                _B,
                "Every interactive component must be keyboard-operable with a visible focus "
                "state.",
                "Accessibility is non-negotiable for an enterprise storefront.",
                cite(ProvenanceKind.UX_STRATEGY, ProvenanceKind.PSYCHOLOGY),
            ),
            self._c(
                ConstraintKind.PERFORMANCE,
                _R,
                "Components must respect their performance budget (lazy-load below the fold, "
                "bounded DOM).",
                "Performance is a conversion factor on commerce storefronts.",
                cite(ProvenanceKind.BUSINESS_STRATEGY, ProvenanceKind.KNOWLEDGE),
            ),
        ]
        if draft.theme_set.has_dark:
            constraints.append(
                self._c(
                    ConstraintKind.THEME_PARITY,
                    _B,
                    "Light and dark themes must theme the same semantic tokens (full parity).",
                    "A half-finished dark mode is worse than none.",
                    cite(ProvenanceKind.CREATIVE_DIRECTOR, ProvenanceKind.KNOWLEDGE),
                )
            )
        if draft.localization.supports_rtl:
            constraints.append(
                self._c(
                    ConstraintKind.RTL_MIRROR,
                    _B,
                    "Directional properties must use logical values so layouts mirror under RTL.",
                    "RTL markets require mirrored layouts, not flipped text alone.",
                    cite(ProvenanceKind.INFORMATION_ARCHITECTURE, ProvenanceKind.KNOWLEDGE),
                )
            )
        return ConstraintSet.of(constraints)

    def _min_contrast(self, draft: DesignSystemDraft) -> float:
        contrasts = [s.accessibility.min_contrast for s in draft.component_specs]
        return min(contrasts) if contrasts else 4.5

    def _c(
        self,
        kind: ConstraintKind,
        enforcement: EnforcementLevel,
        statement: str,
        rationale: str,
        citations: tuple[Citation, ...],
        parameters: dict[str, str] | None = None,
    ) -> Constraint:
        return Constraint(
            id=ConstraintId.new(),
            kind=kind,
            enforcement=enforcement,
            statement=statement,
            rationale=rationale,
            parameters=parameters or {},
            citations=citations,
        )

    def _citation_picker(self, evidence: EvidenceGraph):
        by_prov: dict[ProvenanceKind, list[DSEvidence]] = {}
        for item in evidence:
            by_prov.setdefault(item.provenance, []).append(item)

        def pick(*preferred: ProvenanceKind) -> tuple[Citation, ...]:
            for provenance in preferred:
                bucket = by_prov.get(provenance)
                if bucket:
                    return (Citation(evidence_id=bucket[0].id, relevance="grounds this rule"),)
            # fall back to any evidence so the rule is still grounded
            for bucket in by_prov.values():
                if bucket:
                    return (Citation(evidence_id=bucket[0].id, relevance="grounds this rule"),)
            return ()

        return pick
