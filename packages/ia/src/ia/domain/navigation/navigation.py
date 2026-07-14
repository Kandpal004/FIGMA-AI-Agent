"""Navigation — the global nav, mega menu, footer, and breadcrumb structure.

:class:`Navigation` groups the storefront's navigation surfaces: the global navigation, an
optional mega menu (for category-rich catalogs), the footer columns, and the breadcrumb
strategy, plus utility navigation (search/account/cart/wishlist). Every navigation item's
target resolves to a page in the site map (checked by the report aggregate). Cited.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from ia.domain.navigation.nav_item import NavItem
from ia.domain.shared.ids import IAEvidenceId
from ia.domain.shared.value_objects import PageType

__all__ = [
    "Breadcrumbs",
    "Footer",
    "GlobalNavigation",
    "InvalidNavigationError",
    "MegaMenu",
    "Navigation",
]


class InvalidNavigationError(DesignDirectorError):
    """Raised when navigation is constructed with invalid data."""

    code = "invalid_navigation"
    http_status = 422


@dataclass(frozen=True, slots=True)
class GlobalNavigation:
    """The primary navigation.

    Attributes:
        items: The top-level navigation items.
        principles: Navigation principles the structure honours.
        evidence_ids: The evidence supporting it.
    """

    items: tuple[NavItem, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class MegaMenu:
    """A mega menu of category columns (``enabled=False`` when not used).

    Attributes:
        enabled: Whether the storefront uses a mega menu.
        columns: The columns of navigation items.
        evidence_ids: The evidence supporting it.
    """

    enabled: bool = False
    columns: tuple[NavItem, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Footer:
    """The footer navigation columns.

    Attributes:
        columns: The footer column groups (each a NavItem with children).
        evidence_ids: The evidence supporting it.
    """

    columns: tuple[NavItem, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Breadcrumbs:
    """The breadcrumb strategy.

    Attributes:
        enabled: Whether breadcrumbs are used.
        strategy: How the breadcrumb trail is derived (e.g. "category hierarchy").
        shown_on: The page types breadcrumbs appear on.
        evidence_ids: The evidence supporting it.
    """

    enabled: bool = True
    strategy: str = ""
    shown_on: tuple[PageType, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "shown_on", tuple(self.shown_on))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Navigation:
    """The consolidated, cited navigation structure.

    Attributes:
        global_nav: The primary navigation.
        mega_menu: The mega menu (optional).
        footer: The footer.
        breadcrumbs: The breadcrumb strategy.
        utility: Utility navigation items (search/account/cart/wishlist).
    """

    global_nav: GlobalNavigation = field(default_factory=GlobalNavigation)
    mega_menu: MegaMenu = field(default_factory=MegaMenu)
    footer: Footer = field(default_factory=Footer)
    breadcrumbs: Breadcrumbs = field(default_factory=Breadcrumbs)
    utility: tuple[NavItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "utility", tuple(self.utility))

    def all_items(self) -> tuple[NavItem, ...]:
        return (
            *self.global_nav.items, *self.mega_menu.columns, *self.footer.columns, *self.utility
        )

    def targets(self) -> frozenset[PageType]:
        """Every page type any navigation item targets."""
        return frozenset(t for item in self.all_items() for t in item.targets())

    def evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return (
            *self.global_nav.evidence_ids, *self.mega_menu.evidence_ids,
            *self.footer.evidence_ids, *self.breadcrumbs.evidence_ids,
            *(eid for item in self.all_items() for eid in item.all_evidence_ids()),
        )
