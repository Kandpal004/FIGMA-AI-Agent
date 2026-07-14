"""The Brand Identity — the consolidated core of who the brand is.

:class:`BrandIdentity` groups the outputs of identity synthesis — positioning, mission,
vision, values, promise, and story — into one cohesive, cited value object the report
composes.

Pure domain: standard library and the identity sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.identity.positioning import BrandPositioning
from brand.domain.identity.purpose import BrandMission, BrandPromise, BrandVision
from brand.domain.identity.story import BrandStory
from brand.domain.identity.values import BrandValues
from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["BrandIdentity"]


@dataclass(frozen=True, slots=True)
class BrandIdentity:
    """The consolidated, cited brand identity core.

    Attributes:
        positioning: The space the brand owns.
        mission: Why the brand exists.
        vision: The future it works toward.
        promise: What customers can always count on.
        values: The principles the brand holds.
        story: The brand narrative.
    """

    positioning: BrandPositioning
    mission: BrandMission
    vision: BrandVision
    promise: BrandPromise
    values: BrandValues
    story: BrandStory

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (
            *self.positioning.evidence_ids,
            *self.mission.evidence_ids,
            *self.vision.evidence_ids,
            *self.promise.evidence_ids,
            *self.values.evidence_ids(),
            *self.story.evidence_ids,
        )
