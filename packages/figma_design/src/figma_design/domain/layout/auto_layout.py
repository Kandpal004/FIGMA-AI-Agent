"""The Auto Layout model — how a frame arranges its children the way a designer builds it.

An :class:`AutoLayout` is the auto-layout configuration of a FRAME / COMPONENT / INSTANCE node:
the direction, the primary- and counter-axis sizing (HUG / FILL / FIXED), the alignment along
each axis, the item spacing (a gap variable key), the padding (spacing variable keys), and
whether it wraps. Nested auto-layout is simply a child frame carrying its own :class:`AutoLayout`.

It is token-first: ``item_spacing_token`` and the padding reference Design-System spacing
variables, never literals — so a downstream renderer binds Figma variables. Structural rules a
renderer relies on are enforced here (``SPACE_BETWEEN`` needs the intent of multiple children;
sizing is a coherent pair), while cross-node rules (a FILL child requires an auto-layout parent)
are enforced by the tree aggregate.

Pure domain: standard library, the shared-kernel error base, geometry, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import DesignDirectorError

from figma_design.domain.geometry.geometry import Padding
from figma_design.domain.shared.value_objects import AxisAlign, LayoutMode, SizingMode

__all__ = ["AutoLayout", "InvalidAutoLayoutError"]

_TOKEN_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidAutoLayoutError(DesignDirectorError):
    """Raised when an auto-layout is constructed with invalid data."""

    code = "invalid_figma_design_auto_layout"
    http_status = 422


@dataclass(frozen=True, slots=True)
class AutoLayout:
    """The auto-layout configuration of a frame.

    Attributes:
        mode: The layout direction (horizontal / vertical / wrap). Never NONE — a node without
            auto-layout simply carries no :class:`AutoLayout`.
        primary_axis_sizing: How the frame sizes along its layout axis.
        counter_axis_sizing: How the frame sizes across its layout axis.
        primary_align: Distribution along the layout axis.
        counter_align: Alignment across the layout axis.
        item_spacing_token: The spacing variable key used between children.
        padding: The four-sided padding, as spacing variable keys.
        wrap: Whether children wrap to a new line (only meaningful for WRAP mode).
    """

    mode: LayoutMode
    primary_axis_sizing: SizingMode = SizingMode.HUG
    counter_axis_sizing: SizingMode = SizingMode.HUG
    primary_align: AxisAlign = AxisAlign.MIN
    counter_align: AxisAlign = AxisAlign.MIN
    item_spacing_token: str = "space.4"
    padding: Padding = Padding.uniform("space.4")
    wrap: bool = False

    def __post_init__(self) -> None:
        if self.mode is LayoutMode.NONE:
            raise InvalidAutoLayoutError(
                "AutoLayout.mode must not be NONE; omit AutoLayout for a non-auto-layout node."
            )
        token = self.item_spacing_token.strip().lower()
        if not _TOKEN_KEY.match(token):
            raise InvalidAutoLayoutError(
                "AutoLayout.item_spacing_token must reference a dotted spacing token.",
                details={"token": self.item_spacing_token},
            )
        object.__setattr__(self, "item_spacing_token", token)
        if self.counter_align is AxisAlign.SPACE_BETWEEN:
            raise InvalidAutoLayoutError(
                "SPACE_BETWEEN is only valid on the primary axis (primary_align)."
            )
        if self.wrap and self.mode is not LayoutMode.WRAP:
            raise InvalidAutoLayoutError("wrap is only valid when mode is WRAP.")

    @property
    def spacing_token_keys(self) -> tuple[str, ...]:
        """Every spacing variable key this auto-layout binds (gap + padding)."""
        return tuple(dict.fromkeys((self.item_spacing_token, *self.padding.token_keys)))
