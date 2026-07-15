"""The Figma Page model — a page of a professionally-structured file.

A :class:`FigmaPage` is one page in the Figma file: a kind (Cover, Design System, Components,
Flows, or a storefront Page), a name, and the :class:`FigmaTree` of layers it holds. The engine
organizes pages the way a senior designer does — a Cover, a Design System page (variables +
styles), a Components page (component sets), and one page per storefront page — so a
:class:`FigmaPage` is the unit the model versions and a renderer creates.

Pure domain: standard library, the shared-kernel error base, FD ids, the node tree, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.node.node import FigmaTree
from figma_design.domain.shared.ids import FigmaPageId
from figma_design.domain.shared.value_objects import FigmaPageKind

__all__ = ["FigmaPage", "InvalidPageError"]


class InvalidPageError(DesignDirectorError):
    """Raised when a Figma page is constructed with invalid data."""

    code = "invalid_figma_design_page"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FigmaPage:
    """One page in the Figma file.

    Attributes:
        id: Page identity.
        kind: The role the page plays in the file.
        name: The page name (typically with an emoji prefix, e.g. "📄 Homepage").
        order: The 1-based position of the page in the file.
        tree: The layer tree of this page.
    """

    id: FigmaPageId
    kind: FigmaPageKind
    name: str
    order: int
    tree: FigmaTree

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidPageError("FigmaPage.name must be non-empty.")
        if not isinstance(self.order, int) or isinstance(self.order, bool) or self.order < 1:
            raise InvalidPageError("FigmaPage.order must be an int >= 1.")
        object.__setattr__(self, "name", self.name.strip())

    @property
    def node_count(self) -> int:
        return len(self.tree)

    @property
    def evidence_ids(self) -> tuple:
        return self.tree.evidence_ids()
