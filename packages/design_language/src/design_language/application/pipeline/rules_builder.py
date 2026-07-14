"""Stage — Rules construction.

Derives the language's consistency rules, composition rules, and visual constraints from the
validated draft. Consistency rules bind the token ramps and DNA into invariants; composition
rules govern how elements combine; constraints are the hard boundaries that guard restraint and
timelessness — the accent/decoration limits, spacing floor, motion ceiling, trend avoidance,
and generic-pattern ban that are the engine's teeth against the AI-generated look. Every rule
cites the evidence that justifies it, so the discipline is reasoned, never arbitrary.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_language.application.contracts import LanguageDraft
from design_language.domain.evidence.evidence import DLEvidence, EvidenceGraph
from design_language.domain.rules.composition import CompositionRule, CompositionRuleSet
from design_language.domain.rules.consistency import ConsistencyRule, ConsistencyRuleSet
from design_language.domain.rules.constraint import ConstraintSet, VisualConstraint
from design_language.domain.shared.ids import ConstraintId, DLEvidenceId, RuleId
from design_language.domain.shared.value_objects import (
    CompositionKind,
    ConsistencyKind,
    ConstraintKind,
)

__all__ = ["RulesBuilder"]


class RulesBuilder:
    """Derives the consistency/composition/constraint rules from a draft."""

    def build(
        self, draft: LanguageDraft, evidence: EvidenceGraph
    ) -> tuple[ConsistencyRuleSet, CompositionRuleSet, ConstraintSet]:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        return (
            self._consistency(draft, ranked),
            self._composition(draft, ranked),
            self._constraints(draft, ranked),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[DLEvidence], keywords: Sequence[str], limit: int = 1
    ) -> tuple[DLEvidenceId, ...]:
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]
        matched = [
            e for e in ranked
            if any(k in f"{e.claim} {' '.join(t.value for t in e.tags)}".lower() for k in kws)
        ]
        chosen = matched[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)

    def _consistency(
        self, draft: LanguageDraft, ranked: Sequence[DLEvidence]
    ) -> ConsistencyRuleSet:
        tokens = draft.tokens
        dna = draft.visual_dna
        rules = [
            ConsistencyRule(
                id=RuleId.new(), kind=ConsistencyKind.SPACING_RHYTHM,
                statement=f"All spacing derives from the {tokens.spacing.base_unit}-unit modular ramp.",
                evidence_ids=self._cite(ranked, ("spacing", "rhythm", "grid", "system")),
            ),
            ConsistencyRule(
                id=RuleId.new(), kind=ConsistencyKind.TYPE_SCALE,
                statement=f"Type follows a single {tokens.type_scale.ratio.value} modular ratio.",
                evidence_ids=self._cite(ranked, ("type", "typography", "scale", "hierarchy")),
            ),
            ConsistencyRule(
                id=RuleId.new(), kind=ConsistencyKind.CONTRAST,
                statement=f"Contrast holds a {dna.contrast.value} posture with a "
                          f"{tokens.contrast.text_min} text target.",
                evidence_ids=self._cite(ranked, ("contrast", "accessibility", "legibility")),
            ),
            ConsistencyRule(
                id=RuleId.new(), kind=ConsistencyKind.ELEVATION,
                statement=f"Elevation uses {tokens.elevation.levels} levels "
                          f"({tokens.elevation.posture}).",
                evidence_ids=self._cite(ranked, ("elevation", "depth", "shadow", "surface")),
            ),
            ConsistencyRule(
                id=RuleId.new(), kind=ConsistencyKind.ALIGNMENT,
                statement=f"Everything aligns to the {draft.grid_system.alignment.value} grid.",
                evidence_ids=self._cite(ranked, ("alignment", "grid", "structure")),
            ),
            ConsistencyRule(
                id=RuleId.new(), kind=ConsistencyKind.COLOR_ROLE,
                statement=f"Colour uses the {tokens.color.strategy.value} strategy with "
                          f"{tokens.color.accent_count} accent hue(s).",
                evidence_ids=self._cite(ranked, ("color", "colour", "brand", "palette")),
            ),
        ]
        return ConsistencyRuleSet.of(rules)

    def _composition(
        self, draft: LanguageDraft, ranked: Sequence[DLEvidence]
    ) -> CompositionRuleSet:
        rules = [
            CompositionRule(
                id=RuleId.new(), kind=CompositionKind.GRID,
                statement=f"Compose on the {draft.grid_system.columns}-column grid.",
                evidence_ids=self._cite(ranked, ("grid", "layout", "structure")),
            ),
            CompositionRule(
                id=RuleId.new(), kind=CompositionKind.HIERARCHY,
                statement="Establish one clear visual hierarchy per view.",
                evidence_ids=self._cite(ranked, ("hierarchy", "focus", "priority")),
            ),
            CompositionRule(
                id=RuleId.new(), kind=CompositionKind.WHITESPACE,
                statement=f"Whitespace scales with the {draft.visual_dna.density.value} density "
                          f"and luxury level.",
                evidence_ids=self._cite(ranked, ("whitespace", "spacing", "luxury", "premium")),
            ),
            CompositionRule(
                id=RuleId.new(), kind=CompositionKind.FOCAL_POINT,
                statement="Anchor a single focal point per view.",
                evidence_ids=self._cite(ranked, ("focal", "conversion", "attention", "hierarchy")),
            ),
        ]
        return CompositionRuleSet.of(rules)

    def _constraints(
        self, draft: LanguageDraft, ranked: Sequence[DLEvidence]
    ) -> ConstraintSet:
        tokens = draft.tokens
        traits = ", ".join(t.value for t in draft.visual_dna.traits) or "the DNA's traits"
        constraints = [
            VisualConstraint(
                id=ConstraintId.new(), kind=ConstraintKind.ACCENT_LIMIT,
                statement=f"At most {tokens.color.accent_count} accent hue(s).",
                boundary=f"accent_count <= {tokens.color.accent_count}",
                rationale="Restraint keeps the language premium and timeless.",
                evidence_ids=self._cite(ranked, ("color", "restraint", "premium", "brand")),
            ),
            VisualConstraint(
                id=ConstraintId.new(), kind=ConstraintKind.SPACING_FLOOR,
                statement="No spacing below the modular base unit.",
                boundary=f"spacing >= {tokens.spacing.base_unit}",
                rationale="A spacing floor preserves rhythm and breathing room.",
                evidence_ids=self._cite(ranked, ("spacing", "rhythm", "whitespace")),
            ),
            VisualConstraint(
                id=ConstraintId.new(), kind=ConstraintKind.MOTION_CEILING,
                statement=f"Motion stays {tokens.motion.easing}; no gratuitous animation.",
                boundary=f"easing = {tokens.motion.easing}",
                rationale="Restrained motion reads as considered, not gimmicky.",
                evidence_ids=self._cite(ranked, ("motion", "animation", "restraint")),
            ),
            VisualConstraint(
                id=ConstraintId.new(), kind=ConstraintKind.CONTRAST_FLOOR,
                statement=f"Text contrast never falls below {tokens.contrast.text_min}.",
                boundary=f"text_contrast >= {tokens.contrast.text_min}",
                rationale="Legibility is non-negotiable for premium credibility.",
                evidence_ids=self._cite(ranked, ("contrast", "accessibility", "legibility")),
            ),
            VisualConstraint(
                id=ConstraintId.new(), kind=ConstraintKind.TREND_AVOIDANCE,
                statement="Avoid trend-driven decoration; favour timeless restraint.",
                boundary="no ephemeral trends",
                rationale="Trends date; a timeless language endures.",
                evidence_ids=self._cite(ranked, ("timeless", "restraint", "premium", "brand")),
            ),
            VisualConstraint(
                id=ConstraintId.new(), kind=ConstraintKind.GENERIC_PATTERN_BAN,
                statement=f"Reject undifferentiated stock layouts; the DNA traits ({traits}) "
                          f"must be legible in every composition.",
                boundary="no generic AI-pattern layouts",
                rationale="A generic, purpose-free look is the AI tell the language must avoid.",
                evidence_ids=self._cite(ranked, ("brand", "differentiation", "distinct", "identity")),
            ),
        ]
        return ConstraintSet.of(constraints)
