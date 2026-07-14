"""The Brand Verbal System — the consolidated language and copy direction.

:class:`BrandVerbalSystem` groups the language rules and copy guidelines into one
cohesive, cited value object the report composes.

Pure domain: standard library and the verbal sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.verbal.copy_guidelines import BrandCopyGuidelines
from brand.domain.verbal.language_rules import BrandLanguageRules

__all__ = ["BrandVerbalSystem"]


@dataclass(frozen=True, slots=True)
class BrandVerbalSystem:
    """The consolidated, cited verbal system.

    Attributes:
        language_rules: The grammar the brand writes by.
        copy_guidelines: The rules for how the brand writes.
    """

    language_rules: BrandLanguageRules
    copy_guidelines: BrandCopyGuidelines

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (*self.language_rules.evidence_ids, *self.copy_guidelines.evidence_ids)
