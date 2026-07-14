"""The Brand Governance — the consolidated rule system that keeps the brand coherent.

:class:`BrandGovernance` groups the consistency, governance, and validation rule sets
into one cohesive, cited value object the report composes. Together they turn the brand
from a description into an enforceable constitution.

Pure domain: standard library and the governance sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from brand.domain.governance.consistency import ConsistencyRuleSet
from brand.domain.governance.governance import GovernanceRuleSet
from brand.domain.governance.validation import ValidationRuleSet
from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["BrandGovernance"]


@dataclass(frozen=True, slots=True)
class BrandGovernance:
    """The consolidated, cited brand rule system.

    Attributes:
        consistency: The cross-element consistency rules.
        governance: The ownership and change-control rules.
        validation: The machine-checkable validation rules.
    """

    consistency: ConsistencyRuleSet = field(default_factory=ConsistencyRuleSet)
    governance: GovernanceRuleSet = field(default_factory=GovernanceRuleSet)
    validation: ValidationRuleSet = field(default_factory=ValidationRuleSet)

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (
            *self.consistency.evidence_ids(),
            *self.governance.evidence_ids(),
            *self.validation.evidence_ids(),
        )
