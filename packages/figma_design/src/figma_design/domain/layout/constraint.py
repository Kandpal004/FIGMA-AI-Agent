"""The Layout Constraint model — how a non-auto-layout node pins to its parent.

Nodes that are *not* inside an auto-layout frame instead carry a :class:`LayoutConstraint`: how
they pin horizontally and vertically as the parent resizes (left/center/right/stretch/scale). A
senior designer sets these deliberately (a header stretches, a badge pins top-right), so responsive
frames reflow correctly. Auto-layout nodes do not carry constraints; the two are mutually
exclusive on a node.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from figma_design.domain.shared.value_objects import LayoutConstraintKind

__all__ = ["LayoutConstraint"]


@dataclass(frozen=True, slots=True)
class LayoutConstraint:
    """How a node pins to its parent along each axis.

    Attributes:
        horizontal: Horizontal pin/stretch/scale.
        vertical: Vertical pin/stretch/scale.
    """

    horizontal: LayoutConstraintKind = LayoutConstraintKind.MIN
    vertical: LayoutConstraintKind = LayoutConstraintKind.MIN

    @classmethod
    def stretch(cls) -> LayoutConstraint:
        return cls(
            horizontal=LayoutConstraintKind.STRETCH, vertical=LayoutConstraintKind.STRETCH
        )
