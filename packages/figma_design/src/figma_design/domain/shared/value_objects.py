"""Shared value objects for the Figma Design Engine.

These immutable, self-validating value objects are the vocabulary the engine models a Figma file
in: the provenance of the evidence it cites, the Figma node types, the auto-layout modes and
sizing, the layout constraints, the variable types/scopes/collection kinds, the style/paint/
effect kinds, the component-property types, the device classes and page kinds, the kinds of graph
it builds, and the calibrated scales it scores on.

Everything here is pure domain: only the standard library and the shared-kernel error base
(:mod:`core.errors`). No framework, no I/O, no import of any provider or other engine, and — by
design — no import of any Figma SDK, MCP client, or HTTP library. This engine models the Figma
*semantics*; it renders nothing.

Testing considerations
----------------------
* :class:`GraphKind` has exactly five members; :class:`SizingMode` and :class:`LayoutMode` have
  the expected members.
* :class:`Confidence`, :class:`Score`, :class:`Percentage`, and :class:`Priority` validate their
  ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AxisAlign",
    "BlendMode",
    "CollectionKind",
    "ComponentPropertyType",
    "Confidence",
    "ConsideredAlternative",
    "DeviceClass",
    "EffectType",
    "FigmaPageKind",
    "GraphKind",
    "GraphRelation",
    "InvalidFDValueError",
    "LayoutConstraintKind",
    "LayoutMode",
    "NodeKind",
    "NodeType",
    "PaintType",
    "Percentage",
    "Priority",
    "ProvenanceKind",
    "QualityBand",
    "Rank",
    "Score",
    "SizingMode",
    "StyleType",
    "Tag",
    "VariableScope",
    "VariableType",
]


class InvalidFDValueError(DesignDirectorError):
    """Raised when a Figma Design value object is constructed with invalid data."""

    code = "invalid_figma_design_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates — the upstream engines."""

    DESIGN_ORCHESTRATOR = "design_orchestrator"
    DESIGN_SYSTEM = "design_system"
    COMPONENT_INTELLIGENCE = "component_intelligence"
    DESIGN_LANGUAGE = "design_language"
    CREATIVE_DIRECTOR = "creative_director"
    KNOWLEDGE = "knowledge"
    FIGMA = "figma"
    ANALYTICS = "analytics"


# --------------------------------------------------------------------------- #
# Node types                                                                   #
# --------------------------------------------------------------------------- #
class NodeType(str, Enum):
    """A Figma node type."""

    PAGE = "page"
    SECTION = "section"
    FRAME = "frame"
    GROUP = "group"
    COMPONENT = "component"
    COMPONENT_SET = "component_set"
    INSTANCE = "instance"
    TEXT = "text"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    VECTOR = "vector"
    LINE = "line"
    IMAGE = "image"
    ICON = "icon"
    BOOLEAN_OPERATION = "boolean_operation"
    MASK_GROUP = "mask_group"


# --------------------------------------------------------------------------- #
# Auto layout & constraints                                                    #
# --------------------------------------------------------------------------- #
class LayoutMode(str, Enum):
    """An auto-layout direction (NONE = not an auto-layout frame)."""

    NONE = "none"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    WRAP = "wrap"


class SizingMode(str, Enum):
    """How a node sizes along an axis."""

    FIXED = "fixed"
    HUG = "hug"
    FILL = "fill"


class AxisAlign(str, Enum):
    """Alignment/distribution along an auto-layout axis."""

    MIN = "min"
    CENTER = "center"
    MAX = "max"
    SPACE_BETWEEN = "space_between"
    BASELINE = "baseline"


class LayoutConstraintKind(str, Enum):
    """How a non-auto-layout node is pinned to its parent along an axis."""

    MIN = "min"
    CENTER = "center"
    MAX = "max"
    STRETCH = "stretch"
    SCALE = "scale"


# --------------------------------------------------------------------------- #
# Variables                                                                    #
# --------------------------------------------------------------------------- #
class VariableType(str, Enum):
    """A Figma variable's resolved type."""

    COLOR = "color"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"


class VariableScope(str, Enum):
    """Where a variable is allowed to be bound."""

    ALL = "all"
    GAP = "gap"
    WIDTH_HEIGHT = "width_height"
    CORNER_RADIUS = "corner_radius"
    FILL_COLOR = "fill_color"
    STROKE_COLOR = "stroke_color"
    FONT_SIZE = "font_size"
    LINE_HEIGHT = "line_height"
    LETTER_SPACING = "letter_spacing"
    OPACITY = "opacity"
    EFFECT = "effect"
    TEXT_CONTENT = "text_content"


class CollectionKind(str, Enum):
    """The role a variable collection plays in the file."""

    PRIMITIVE = "primitive"
    SEMANTIC = "semantic"
    COMPONENT = "component"
    THEME = "theme"
    DEVICE = "device"


# --------------------------------------------------------------------------- #
# Styles                                                                        #
# --------------------------------------------------------------------------- #
class StyleType(str, Enum):
    """A published style type."""

    FILL = "fill"
    TEXT = "text"
    EFFECT = "effect"
    GRID = "grid"


class PaintType(str, Enum):
    """A paint type."""

    SOLID = "solid"
    GRADIENT_LINEAR = "gradient_linear"
    GRADIENT_RADIAL = "gradient_radial"
    IMAGE = "image"


class EffectType(str, Enum):
    """An effect type."""

    DROP_SHADOW = "drop_shadow"
    INNER_SHADOW = "inner_shadow"
    LAYER_BLUR = "layer_blur"
    BACKGROUND_BLUR = "background_blur"


class BlendMode(str, Enum):
    """A layer blend mode."""

    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"


# --------------------------------------------------------------------------- #
# Components & devices                                                         #
# --------------------------------------------------------------------------- #
class ComponentPropertyType(str, Enum):
    """The type of a component property."""

    VARIANT = "variant"
    BOOLEAN = "boolean"
    TEXT = "text"
    INSTANCE_SWAP = "instance_swap"


class DeviceClass(str, Enum):
    """A responsive device class the model renders frames for."""

    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    ADAPTIVE = "adaptive"


class FigmaPageKind(str, Enum):
    """The role a Figma page plays in a professionally-structured file."""

    COVER = "cover"
    DESIGN_SYSTEM = "design_system"
    COMPONENTS = "components"
    FLOWS = "flows"
    PAGE = "page"


# --------------------------------------------------------------------------- #
# Graphs                                                                       #
# --------------------------------------------------------------------------- #
class GraphKind(str, Enum):
    """One of the five Figma graphs."""

    FIGMA_TREE = "figma_tree"
    COMPONENT = "component"
    AUTO_LAYOUT = "auto_layout"
    VARIABLE = "variable"
    STYLE = "style"


class NodeKind(str, Enum):
    """The kind of node a Figma-graph node represents."""

    NODE = "node"
    COMPONENT = "component"
    COMPONENT_SET = "component_set"
    INSTANCE = "instance"
    VARIABLE = "variable"
    COLLECTION = "collection"
    MODE = "mode"
    STYLE = "style"
    FRAME = "frame"


class GraphRelation(str, Enum):
    """A typed, directed edge between two Figma-graph nodes.

    ``CONTAINS``, ``VARIANT_OF``, ``ALIASES`` and ``DEPENDS_ON`` must be acyclic — the node
    containment, the variant matrix, and the variable alias chains form no cycle.
    """

    CONTAINS = "contains"
    INSTANCE_OF = "instance_of"
    VARIANT_OF = "variant_of"
    BINDS = "binds"
    USES_STYLE = "uses_style"
    ALIASES = "aliases"
    DEPENDS_ON = "depends_on"


class QualityBand(str, Enum):
    """A categorical band shared by the score scales."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


# --------------------------------------------------------------------------- #
# Calibrated scales                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """A confidence value in ``[0, 1]``."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidFDValueError(
                "Confidence.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(1.0, max(0.0, value)))


@dataclass(frozen=True, slots=True, order=True)
class Percentage:
    """A fraction in ``[0, 1]`` (e.g. a coverage or grounding ratio)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidFDValueError(
                "Percentage.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def ratio(cls, present: int, total: int) -> Self:
        """The fraction ``present / total`` (1.0 when nothing is expected)."""
        if total <= 0:
            return cls(value=1.0)
        return cls(value=min(1.0, max(0.0, present / total)))


@dataclass(frozen=True, slots=True, order=True)
class Score:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidFDValueError(
                "Score.value must be within [0, 100].", details={"value": self.value}
            )

    @property
    def band(self) -> QualityBand:
        if self.value >= 80.0:
            return QualityBand.EXCELLENT
        if self.value >= 60.0:
            return QualityBand.GOOD
        if self.value >= 40.0:
            return QualityBand.FAIR
        return QualityBand.POOR

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(100.0, max(0.0, value)))


def _bounded_int(name: str, value: int, low: int, high: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidFDValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidFDValueError(
            f"{name} must be within [{low}, {high}].", details={"value": value}
        )
    return value


@dataclass(frozen=True, slots=True, order=True)
class Priority:
    """A 1–5 priority (5 = highest)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Priority", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Rank:
    """A 1-based ordinal rank (1 = first)."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 1:
            raise InvalidFDValueError("Rank must be an int >= 1.", details={"value": self.value})

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A choice the engine weighed and rejected — the trade-off record.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidFDValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidFDValueError(
                "ConsideredAlternative.reason_rejected must be non-empty."
            )


_TAG_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Tag:
    """A normalized free-form label (lower case, whitespace collapsed to hyphens)."""

    value: str

    def __post_init__(self) -> None:
        normalized = _TAG_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidFDValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
