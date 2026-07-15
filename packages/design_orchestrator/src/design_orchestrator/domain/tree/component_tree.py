"""The component tree — the rooted, ordered hierarchy a future Figma phase builds.

A :class:`ComponentTree` mirrors the node tree P18 will create: a single ROOT, PAGE children,
their SECTION children (in section order), each SECTION's COMPONENT, and each COMPONENT's chosen
VARIANT. It is the *structural* view of the plan, complementary to the execution graph's
*temporal* view; both are derived from the same section plans, so they cannot disagree.

The tree validates the guarantees a builder relies on: exactly one root, legal kind nesting
(ROOT → PAGE → SECTION → COMPONENT → VARIANT), every non-root parent resolves, no cycles, and a
stable child order. COMPONENT nodes carry their ``SectionPlanId`` so the token and variant
mappings join straight onto the tree.

Pure domain: standard library, the shared-kernel error base, DO ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.ids import DONodeId, SectionPlanId
from design_orchestrator.domain.shared.value_objects import TreeNodeKind

__all__ = ["ComponentTree", "InvalidComponentTreeError", "TreeNode"]

# Which node kinds may legally nest directly under which parent kind.
_LEGAL_CHILDREN: dict[TreeNodeKind, frozenset[TreeNodeKind]] = {
    TreeNodeKind.ROOT: frozenset({TreeNodeKind.PAGE}),
    TreeNodeKind.PAGE: frozenset({TreeNodeKind.SECTION}),
    TreeNodeKind.SECTION: frozenset({TreeNodeKind.COMPONENT}),
    TreeNodeKind.COMPONENT: frozenset({TreeNodeKind.VARIANT}),
    TreeNodeKind.VARIANT: frozenset(),
}


class InvalidComponentTreeError(DesignDirectorError):
    """Raised when the component tree is structurally invalid."""

    code = "invalid_design_orchestrator_component_tree"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TreeNode:
    """One node in the component tree.

    Attributes:
        id: Node identity.
        kind: The node kind.
        label: A short human-readable label.
        parent_id: The parent node (``None`` only for the root).
        order: The 1-based order among siblings.
        section_ref: The section plan a SECTION/COMPONENT node realises, if any.
        evidence_ids: The evidence supporting the node.
    """

    id: DONodeId
    kind: TreeNodeKind
    label: str
    parent_id: DONodeId | None = None
    order: int = 1
    section_ref: SectionPlanId | None = None
    evidence_ids: tuple = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidComponentTreeError("TreeNode.label must be non-empty.")
        if not isinstance(self.order, int) or isinstance(self.order, bool) or self.order < 1:
            raise InvalidComponentTreeError("TreeNode.order must be an int >= 1.")
        if self.parent_id is not None and self.parent_id == self.id:
            raise InvalidComponentTreeError(
                "A tree node cannot be its own parent.", details={"node": str(self.id)}
            )
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ComponentTree:
    """The rooted, ordered component hierarchy."""

    nodes: Mapping[DONodeId, TreeNode] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, MappingProxyType):
            object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))
        nodes = self.nodes
        if not nodes:
            raise InvalidComponentTreeError("A ComponentTree must have at least a root.")

        roots = [n for n in nodes.values() if n.parent_id is None]
        if len(roots) != 1:
            raise InvalidComponentTreeError(
                "A ComponentTree must have exactly one root.",
                details={"roots": len(roots)},
            )
        root = roots[0]
        if root.kind is not TreeNodeKind.ROOT:
            raise InvalidComponentTreeError("The root node must be of kind ROOT.")

        for node in nodes.values():
            if node.parent_id is None:
                continue
            parent = nodes.get(node.parent_id)
            if parent is None:
                raise InvalidComponentTreeError(
                    "A node references a parent not in the tree.",
                    details={"node": str(node.id)},
                )
            if node.kind not in _LEGAL_CHILDREN[parent.kind]:
                raise InvalidComponentTreeError(
                    f"A {node.kind.value} node cannot nest under a {parent.kind.value} node.",
                    details={"node": str(node.id)},
                )
        if root.kind is TreeNodeKind.ROOT and root.parent_id is not None:
            raise InvalidComponentTreeError("The ROOT node must not have a parent.")

        self._assert_acyclic(root.id)

    def _assert_acyclic(self, root_id: DONodeId) -> None:
        # Walk parent pointers from each node; every chain must terminate at the root without
        # revisiting a node.
        for start in self.nodes:
            seen: set[DONodeId] = set()
            current: DONodeId | None = start
            while current is not None:
                if current in seen:
                    raise InvalidComponentTreeError(
                        "The component tree contains a cycle.", details={"node": str(current)}
                    )
                seen.add(current)
                current = self.nodes[current].parent_id

    @classmethod
    def of(cls, nodes: Iterable[TreeNode]) -> ComponentTree:
        mapping: dict[DONodeId, TreeNode] = {}
        for node in nodes:
            if node.id in mapping:
                raise InvalidComponentTreeError(
                    "Duplicate tree node id.", details={"id": str(node.id)}
                )
            mapping[node.id] = node
        return cls(nodes=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())

    @property
    def root(self) -> TreeNode:
        return next(n for n in self.nodes.values() if n.parent_id is None)

    def children(self, node_id: DONodeId) -> tuple[TreeNode, ...]:
        kids = [n for n in self.nodes.values() if n.parent_id == node_id]
        return tuple(sorted(kids, key=lambda n: n.order))

    def by_kind(self, kind: TreeNodeKind) -> tuple[TreeNode, ...]:
        return tuple(n for n in self.nodes.values() if n.kind is kind)

    def evidence_ids(self) -> tuple:
        return tuple(eid for n in self.nodes.values() for eid in n.evidence_ids)
