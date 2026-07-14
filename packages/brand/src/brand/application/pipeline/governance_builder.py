"""Stage — Governance construction.

Derives the brand's rule system deterministically from the validated draft: the
:class:`ConsistencyRuleSet` that keeps elements aligned, the :class:`GovernanceRuleSet`
that assigns ownership and change control, and the machine-checkable
:class:`ValidationRuleSet` that a downstream Design-System / UI / QA phase enforces
automatically. Each rule cites the brand element it governs, so governance is grounded
in the same evidence as the brand itself.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.application.contracts import BrandDraft
from brand.domain.governance.consistency import (
    BrandConsistencyRule,
    ConsistencyRuleSet,
)
from brand.domain.governance.governance import BrandGovernanceRule, GovernanceRuleSet
from brand.domain.governance.governance_model import BrandGovernance
from brand.domain.governance.validation import BrandValidationRule, ValidationRuleSet
from brand.domain.shared.ids import (
    BrandEvidenceId,
    ConsistencyRuleId,
    GovernanceRuleId,
    ValidationRuleId,
)
from brand.domain.shared.value_objects import (
    ConsistencyDimension,
    GovernanceScope,
    RuleEnforcement,
    ValidationSeverity,
)

__all__ = ["GovernanceBuilder"]


def _first(evidence_ids: Sequence[BrandEvidenceId]) -> tuple[BrandEvidenceId, ...]:
    return (evidence_ids[0],) if evidence_ids else ()


class GovernanceBuilder:
    """Builds the brand governance from a validated draft."""

    def build(self, draft: BrandDraft) -> BrandGovernance:
        return BrandGovernance(
            consistency=self._consistency(draft),
            governance=self._governance(draft),
            validation=self._validation(draft),
        )

    # ------------------------------------------------------------------ #
    def _consistency(self, draft: BrandDraft) -> ConsistencyRuleSet:
        v = draft.visual
        specs: list[tuple[ConsistencyDimension, str, Sequence[BrandEvidenceId]]] = [
            (ConsistencyDimension.VOICE,
             "The brand voice stays within its defined tone-of-voice dimensions across every touchpoint.",
             draft.character.voice.evidence_ids),
            (ConsistencyDimension.TONE,
             "Tone modulates only within the defined contextual adjustments; the underlying voice never changes.",
             draft.character.tone.evidence_ids),
            (ConsistencyDimension.COLOR,
             f"Colour honours the {v.color.temperament.value} temperament; the accent is reserved for its defined role.",
             v.color.evidence_ids),
            (ConsistencyDimension.TYPOGRAPHY,
             "Typography uses only the defined display and body voices, per the hierarchy intent.",
             v.typography.evidence_ids),
            (ConsistencyDimension.SPACING,
             f"Layouts express the {v.spacing.density.value} spacing density.",
             v.spacing.evidence_ids),
            (ConsistencyDimension.MOTION,
             "Motion stays within its defined character and restraint.",
             v.motion.evidence_ids),
            (ConsistencyDimension.IMAGERY,
             f"Imagery keeps the {v.photography.treatment.value} treatment.",
             v.photography.evidence_ids),
            (ConsistencyDimension.TERMINOLOGY,
             "Copy uses the brand's canonical terminology and preferred words.",
             draft.verbal.language_rules.evidence_ids),
        ]
        rules = [
            BrandConsistencyRule(
                id=ConsistencyRuleId.new(), dimension=dimension, rule=rule,
                enforcement=RuleEnforcement.MUST, evidence_ids=_first(ev),
            )
            for dimension, rule, ev in specs
            if ev
        ]
        return ConsistencyRuleSet.of(rules)

    def _governance(self, draft: BrandDraft) -> GovernanceRuleSet:
        specs: list[tuple[GovernanceScope, str, str, Sequence[BrandEvidenceId]]] = [
            (GovernanceScope.IDENTITY,
             "Changes to positioning, mission, or values require brand-owner sign-off.",
             "Brand Owner", draft.identity.positioning.evidence_ids),
            (GovernanceScope.VISUAL,
             "Changes to the visual direction require design-lead approval against this brand.",
             "Design Lead", draft.visual.evidence_ids()),
            (GovernanceScope.VERBAL,
             "Changes to voice, language, or copy rules require content-lead approval.",
             "Content Lead", draft.verbal.evidence_ids()),
        ]
        rules = [
            BrandGovernanceRule(
                id=GovernanceRuleId.new(), scope=scope, rule=rule, owner=owner,
                enforcement=RuleEnforcement.MUST, evidence_ids=_first(ev),
            )
            for scope, rule, owner, ev in specs
            if ev
        ]
        return GovernanceRuleSet.of(rules)

    def _validation(self, draft: BrandDraft) -> ValidationRuleSet:
        v = draft.visual
        specs: list[tuple[str, str, str, Sequence[BrandEvidenceId]]] = [
            ("primary_cta",
             "Every primary call-to-action MUST express the defined component personality.",
             "cta.weight == component_personality.emphasis", v.component.evidence_ids),
            ("copy",
             "Copy MUST NOT use any forbidden word and MUST follow the language rules.",
             "no forbidden_words in copy", draft.verbal.language_rules.evidence_ids),
            ("contrast",
             f"Colour contrast MUST satisfy the {v.color.contrast.value} contrast level.",
             f"contrast >= {v.color.contrast.value}", v.color.evidence_ids),
            ("typography",
             "Typography MUST use only the defined display and body type voices.",
             "font.voice in {display_voice, body_voice}", v.typography.evidence_ids),
            ("motion",
             "Motion MUST honour the defined character and restraint.",
             "motion.character == defined and respects restraint", v.motion.evidence_ids),
        ]
        rules = [
            BrandValidationRule(
                id=ValidationRuleId.new(), subject=subject, assertion=assertion,
                enforcement=RuleEnforcement.MUST, severity=ValidationSeverity.ERROR,
                checkable_hint=hint, evidence_ids=_first(ev),
            )
            for subject, assertion, hint, ev in specs
            if ev
        ]
        return ValidationRuleSet.of(rules)
