"""Page priorities — how a page ranks along each structural dimension.

A :class:`PagePriorities` carries a :class:`Priority` for each of the five dimensions the
IA prioritises a page along — navigation, SEO, accessibility, conversion, and mobile — and
derives an overall priority. These drive how much structural weight a page and its sections
receive downstream.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from ia.domain.shared.value_objects import Priority, PriorityDimension

__all__ = ["PagePriorities"]


@dataclass(frozen=True, slots=True)
class PagePriorities:
    """The cited per-dimension priorities of a page.

    Attributes:
        navigation: Navigation priority (how prominent the page is in navigation).
        seo: SEO priority.
        accessibility: Accessibility priority.
        conversion: Conversion priority.
        mobile: Mobile priority.
    """

    navigation: Priority = Priority(3)
    seo: Priority = Priority(3)
    accessibility: Priority = Priority(3)
    conversion: Priority = Priority(3)
    mobile: Priority = Priority(3)

    def get(self, dimension: PriorityDimension) -> Priority:
        return {
            PriorityDimension.NAVIGATION: self.navigation,
            PriorityDimension.SEO: self.seo,
            PriorityDimension.ACCESSIBILITY: self.accessibility,
            PriorityDimension.CONVERSION: self.conversion,
            PriorityDimension.MOBILE: self.mobile,
        }[dimension]

    @property
    def overall(self) -> float:
        """The mean priority across all five dimensions."""
        values = (
            int(self.navigation), int(self.seo), int(self.accessibility),
            int(self.conversion), int(self.mobile),
        )
        return round(sum(values) / len(values), 3)
