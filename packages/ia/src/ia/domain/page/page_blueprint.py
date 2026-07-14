"""Page blueprint — the structural definition of one page.

A :class:`PageBlueprint` is the atomic unit of the information architecture: for one page
it states the purpose, the goals it serves, the required and optional sections in priority
order, the five per-dimension priorities, the primary and secondary actions, and where
trust and conversion sit. Every future wireframe must trace to one of these — this is where
page *structure* is decided, before any layout.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.page.action import PageAction
from ia.domain.page.goals import PageGoals
from ia.domain.page.priorities import PagePriorities
from ia.domain.section.section import Section
from ia.domain.shared.ids import IAEvidenceId, PageBlueprintId
from ia.domain.shared.value_objects import (
    ActionType,
    PageRequirement,
    PageType,
    Placement,
)

__all__ = ["InvalidPageBlueprintError", "PageBlueprint"]


class InvalidPageBlueprintError(DesignDirectorError):
    """Raised when a page blueprint is constructed with invalid data."""

    code = "invalid_page_blueprint"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PageBlueprint:
    """The cited structural blueprint for one page.

    Attributes:
        id: Blueprint identity.
        page_type: Which page type this defines.
        requirement: Whether the page is required or optional.
        purpose: Why the page exists.
        slug_intent: The intended URL slug pattern (structure, not a rendered URL).
        goals: The business and user goals the page serves.
        required_sections: The sections the page must carry, in priority order.
        optional_sections: The sections the page may carry.
        priorities: The page's per-dimension priorities.
        primary_actions: The primary actions the page drives.
        secondary_actions: The secondary actions the page drives.
        trust_placement: Where trust elements sit.
        conversion_placement: Where conversion elements sit.
        evidence_ids: The evidence supporting the blueprint.
    """

    id: PageBlueprintId
    page_type: PageType
    requirement: PageRequirement
    purpose: str
    goals: PageGoals
    slug_intent: str = ""
    required_sections: tuple[Section, ...] = ()
    optional_sections: tuple[Section, ...] = ()
    priorities: PagePriorities = PagePriorities()
    primary_actions: tuple[PageAction, ...] = ()
    secondary_actions: tuple[PageAction, ...] = ()
    trust_placement: Placement = Placement.BELOW_FOLD
    conversion_placement: Placement = Placement.ABOVE_FOLD
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.purpose or not self.purpose.strip():
            raise InvalidPageBlueprintError("PageBlueprint.purpose must be non-empty.")
        for action in self.primary_actions:
            if action.type is not ActionType.PRIMARY:
                raise InvalidPageBlueprintError(
                    "primary_actions must all be PRIMARY.", details={"action": action.action}
                )
        object.__setattr__(self, "required_sections", tuple(self.required_sections))
        object.__setattr__(self, "optional_sections", tuple(self.optional_sections))
        object.__setattr__(self, "primary_actions", tuple(self.primary_actions))
        object.__setattr__(self, "secondary_actions", tuple(self.secondary_actions))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def is_required(self) -> bool:
        return self.requirement is PageRequirement.REQUIRED

    def sections_by_priority(self) -> tuple[Section, ...]:
        """All sections (required first, then optional) in descending priority order."""
        return tuple(
            sorted(
                (*self.required_sections, *self.optional_sections),
                key=lambda s: (s.is_required, int(s.priority)),
                reverse=True,
            )
        )

    def all_evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return (
            *self.evidence_ids,
            *self.goals.evidence_ids,
            *(eid for s in self.required_sections for eid in s.all_evidence_ids()),
            *(eid for s in self.optional_sections for eid in s.all_evidence_ids()),
            *(eid for a in self.primary_actions for eid in a.evidence_ids),
            *(eid for a in self.secondary_actions for eid in a.evidence_ids),
        )
