"""Stage — Component Tree Construction.

Builds the rooted :class:`ComponentTree` from the draft: a single ROOT, one PAGE node per page,
one SECTION node per section (in section order), each SECTION's COMPONENT node (carrying the
section's evidence and its ``SectionPlanId`` so the mappings join on), and each COMPONENT's chosen
VARIANT node. The tree is the structural view a future Figma phase instantiates; it is derived
from the same sections as the execution graph, so the two views cannot disagree.
"""

from __future__ import annotations

from design_orchestrator.application.contracts import ExecutionDraft
from design_orchestrator.domain.tree.component_tree import ComponentTree, TreeNode
from design_orchestrator.domain.shared.ids import DONodeId
from design_orchestrator.domain.shared.value_objects import TreeNodeKind

__all__ = ["TreeBuilder"]


class TreeBuilder:
    """Builds the component tree from the draft's pages and sections."""

    def build(self, draft: ExecutionDraft) -> ComponentTree:
        nodes: list[TreeNode] = []
        root = TreeNode(id=DONodeId.new(), kind=TreeNodeKind.ROOT, label="storefront")
        nodes.append(root)

        for page_index, page in enumerate(draft.pages, start=1):
            page_node = TreeNode(
                id=DONodeId.new(),
                kind=TreeNodeKind.PAGE,
                label=page.page_type.value,
                parent_id=root.id,
                order=page_index,
            )
            nodes.append(page_node)
            for section in page.sections:
                section_node = TreeNode(
                    id=DONodeId.new(),
                    kind=TreeNodeKind.SECTION,
                    label=f"{section.role.value}:{int(section.order)}",
                    parent_id=page_node.id,
                    order=int(section.order),
                    section_ref=section.id,
                    evidence_ids=section.evidence_ids,
                )
                nodes.append(section_node)
                component_node = TreeNode(
                    id=DONodeId.new(),
                    kind=TreeNodeKind.COMPONENT,
                    label=section.component.value,
                    parent_id=section_node.id,
                    order=1,
                    section_ref=section.id,
                    evidence_ids=section.evidence_ids,
                )
                nodes.append(component_node)
                nodes.append(
                    TreeNode(
                        id=DONodeId.new(),
                        kind=TreeNodeKind.VARIANT,
                        label=section.variant_name,
                        parent_id=component_node.id,
                        order=1,
                    )
                )
        return ComponentTree.of(nodes)
