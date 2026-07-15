"""The Figma node model and tree — the Layers-panel structure a designer builds.

A :class:`FigmaNode` is one node in a Figma page's layer tree: typed by :class:`NodeType`, sized
along each axis (HUG/FILL/FIXED), optionally an auto-layout frame (or, if not, pinned by a layout
constraint), optionally carrying a corner radius, fill/effect style references, variable bindings,
typed content (text / image / instance), and developer notes / comments / annotations for handoff.

A :class:`FigmaTree` is the rooted layer tree of one page. It validates the structure a renderer
relies on: exactly one root, legal nesting (a component set contains only components, an instance
is terminal, leaves carry no children), every non-root parent resolves, no containment cycle, and
— the auto-layout rule — a node that FILLs an axis must live inside an auto-layout parent.

Pure domain: standard library, the shared-kernel error base, FD ids, the layout/geometry/content/
annotation value objects, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.geometry.geometry import CornerRadius, Size
from figma_design.domain.layout.auto_layout import AutoLayout
from figma_design.domain.layout.constraint import LayoutConstraint
from figma_design.domain.node.annotation import Annotation, Comment, DeveloperNote
from figma_design.domain.node.content import ImageRef, InstanceRef, TextContent
from figma_design.domain.shared.ids import FDEvidenceId, FigmaNodeId, StyleId
from figma_design.domain.shared.value_objects import NodeType, SizingMode
from figma_design.domain.variable.binding import VariableBinding

__all__ = ["FigmaNode", "FigmaTree", "InvalidNodeError", "InvalidTreeError"]

# Node types that may contain children.
_CONTAINERS: frozenset[NodeType] = frozenset(
    {
        NodeType.SECTION,
        NodeType.FRAME,
        NodeType.GROUP,
        NodeType.COMPONENT,
        NodeType.COMPONENT_SET,
        NodeType.MASK_GROUP,
        NodeType.BOOLEAN_OPERATION,
    }
)
# Node types that may carry auto-layout.
_AUTO_LAYOUT_CAPABLE: frozenset[NodeType] = frozenset(
    {NodeType.FRAME, NodeType.COMPONENT, NodeType.INSTANCE, NodeType.SECTION}
)


class InvalidNodeError(DesignDirectorError):
    """Raised when a Figma node is constructed with invalid data."""

    code = "invalid_figma_design_node"
    http_status = 422


class InvalidTreeError(DesignDirectorError):
    """Raised when a Figma tree violates a structural invariant."""

    code = "invalid_figma_design_tree"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FigmaNode:
    """One node in a Figma page's layer tree.

    Attributes:
        id: Node identity.
        type: The Figma node type.
        name: The layer name.
        parent_id: The parent node (``None`` only for the page's root node).
        order: The 1-based z-order among siblings.
        width: Horizontal sizing.
        height: Vertical sizing.
        auto_layout: The auto-layout config, if this is an auto-layout frame.
        constraint: The pin/scale constraint, if this is not an auto-layout child.
        corner_radius: The corner radius, if any.
        fill_style_ref: The published fill style this node uses, if any.
        effect_style_ref: The published effect style this node uses, if any.
        variable_bindings: The node-property → variable bindings.
        text_content: The content for a TEXT node.
        image_ref: The content for an IMAGE node.
        instance_ref: The content for an INSTANCE node.
        developer_notes: Dev-Mode notes for handoff.
        comments: Design comments pinned to the node.
        annotations: Measurement/spec annotations.
        citations: The evidence supporting this node (must resolve in the evidence graph).
    """

    id: FigmaNodeId
    type: NodeType
    name: str
    parent_id: FigmaNodeId | None = None
    order: int = 1
    width: Size = field(default_factory=Size.hug)
    height: Size = field(default_factory=Size.hug)
    auto_layout: AutoLayout | None = None
    constraint: LayoutConstraint | None = None
    corner_radius: CornerRadius | None = None
    fill_style_ref: StyleId | None = None
    effect_style_ref: StyleId | None = None
    variable_bindings: tuple[VariableBinding, ...] = ()
    text_content: TextContent | None = None
    image_ref: ImageRef | None = None
    instance_ref: InstanceRef | None = None
    developer_notes: tuple[DeveloperNote, ...] = ()
    comments: tuple[Comment, ...] = ()
    annotations: tuple[Annotation, ...] = ()
    citations: tuple = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidNodeError("FigmaNode.name must be non-empty.")
        if not isinstance(self.order, int) or isinstance(self.order, bool) or self.order < 1:
            raise InvalidNodeError("FigmaNode.order must be an int >= 1.")
        if self.parent_id is not None and self.parent_id == self.id:
            raise InvalidNodeError("A node cannot be its own parent.", details={"node": str(self.id)})
        if self.auto_layout is not None:
            if self.type not in _AUTO_LAYOUT_CAPABLE:
                raise InvalidNodeError(
                    f"A {self.type.value} node cannot carry auto-layout.",
                    details={"node": str(self.id)},
                )
            if self.constraint is not None:
                raise InvalidNodeError(
                    "A node cannot carry both auto-layout and a layout constraint.",
                    details={"node": str(self.id)},
                )
        self._validate_content()
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "variable_bindings", tuple(self.variable_bindings))
        object.__setattr__(self, "developer_notes", tuple(self.developer_notes))
        object.__setattr__(self, "comments", tuple(self.comments))
        object.__setattr__(self, "annotations", tuple(self.annotations))
        object.__setattr__(self, "citations", tuple(self.citations))

    def _validate_content(self) -> None:
        if self.type is NodeType.TEXT and self.text_content is None:
            raise InvalidNodeError("A TEXT node requires text content.")
        if self.type is NodeType.IMAGE and self.image_ref is None:
            raise InvalidNodeError("An IMAGE node requires an image ref.")
        if self.type is NodeType.INSTANCE and self.instance_ref is None:
            raise InvalidNodeError("An INSTANCE node requires an instance ref.")
        if self.type is not NodeType.TEXT and self.text_content is not None:
            raise InvalidNodeError("Only a TEXT node may carry text content.")
        if self.type is not NodeType.IMAGE and self.image_ref is not None:
            raise InvalidNodeError("Only an IMAGE node may carry an image ref.")
        if self.type is not NodeType.INSTANCE and self.instance_ref is not None:
            raise InvalidNodeError("Only an INSTANCE node may carry an instance ref.")

    @property
    def is_container(self) -> bool:
        return self.type in _CONTAINERS

    @property
    def fills_axis(self) -> bool:
        return self.width.mode is SizingMode.FILL or self.height.mode is SizingMode.FILL

    @property
    def evidence_ids(self) -> tuple[FDEvidenceId, ...]:
        return tuple(c.evidence_id for c in self.citations)

    @property
    def spacing_token_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        if self.auto_layout is not None:
            keys.extend(self.auto_layout.spacing_token_keys)
        if self.corner_radius is not None:
            keys.append(self.corner_radius.token)
        return tuple(dict.fromkeys(keys))


@dataclass(frozen=True, slots=True)
class FigmaTree:
    """The rooted layer tree of one page."""

    nodes: Mapping[FigmaNodeId, FigmaNode] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        nodes = self.nodes
        if not nodes:
            raise InvalidTreeError("A FigmaTree must have at least a root node.")
        roots = [n for n in nodes.values() if n.parent_id is None]
        if len(roots) != 1:
            raise InvalidTreeError(
                "A FigmaTree must have exactly one root.", details={"roots": len(roots)}
            )
        for node in nodes.values():
            if node.type is NodeType.PAGE:
                raise InvalidTreeError("A PAGE is not a tree node.", details={"node": str(node.id)})
            if node.parent_id is None:
                if node.fills_axis:
                    raise InvalidTreeError(
                        "The root node cannot FILL an axis (no parent to fill).",
                        details={"node": str(node.id)},
                    )
                continue
            parent = nodes.get(node.parent_id)
            if parent is None:
                raise InvalidTreeError(
                    "A node references a parent not in the tree.", details={"node": str(node.id)}
                )
            self._validate_nesting(node, parent)
        self._assert_acyclic()

    def _validate_nesting(self, node: FigmaNode, parent: FigmaNode) -> None:
        if not parent.is_container:
            raise InvalidTreeError(
                f"A {parent.type.value} node cannot contain children.",
                details={"parent": str(parent.id), "child": str(node.id)},
            )
        if parent.type is NodeType.COMPONENT_SET and node.type is not NodeType.COMPONENT:
            raise InvalidTreeError(
                "A COMPONENT_SET may contain only COMPONENT nodes.",
                details={"child": str(node.id)},
            )
        if node.fills_axis and parent.auto_layout is None:
            raise InvalidTreeError(
                "A node may FILL an axis only inside an auto-layout parent.",
                details={"node": str(node.id), "parent": str(parent.id)},
            )

    def _assert_acyclic(self) -> None:
        for start in self.nodes:
            seen: set[FigmaNodeId] = set()
            current: FigmaNodeId | None = start
            while current is not None:
                if current in seen:
                    raise InvalidTreeError(
                        "The node tree contains a cycle.", details={"node": str(current)}
                    )
                seen.add(current)
                current = self.nodes[current].parent_id

    @classmethod
    def of(cls, nodes: Iterable[FigmaNode]) -> FigmaTree:
        mapping: dict[FigmaNodeId, FigmaNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidTreeError("Duplicate node id in tree.", details={"id": str(node.id)})
            mapping[node.id] = node
        return cls(nodes=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    @property
    def root(self) -> FigmaNode:
        return next(n for n in self.nodes.values() if n.parent_id is None)

    def has(self, node_id: FigmaNodeId) -> bool:
        return node_id in self.nodes

    def get(self, node_id: FigmaNodeId) -> FigmaNode:
        node = self.nodes.get(node_id)
        if node is None:
            raise InvalidTreeError(f"Node {node_id} not found.", details={"node_id": str(node_id)})
        return node

    def children(self, node_id: FigmaNodeId) -> tuple[FigmaNode, ...]:
        kids = [n for n in self.nodes.values() if n.parent_id == node_id]
        return tuple(sorted(kids, key=lambda n: n.order))

    def by_type(self, node_type: NodeType) -> tuple[FigmaNode, ...]:
        return tuple(n for n in self.nodes.values() if n.type is node_type)

    def evidence_ids(self) -> tuple[FDEvidenceId, ...]:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
