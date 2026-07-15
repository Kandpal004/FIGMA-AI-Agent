"""FigmaDesignModel — the aggregate the whole engine produces.

An immutable, versioned model: the organized Figma pages and their layer trees, the variable
collections (with modes), the published style set, the component-set catalog, the resolved token
and variant mappings, the five graphs, the evidence graph, and the quality picture. It is the
platform-independent semantic model of a professionally-structured Figma file — it renders nothing
and imports no Figma SDK, MCP client, or HTTP library.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any node, component set, or graph
   node resolves in the model's :class:`EvidenceGraph`. Nothing the engine cannot cite enters the
   model.
2. **Reference integrity** — every variable binding targets a declared variable whose scope
   permits the property; every style reference resolves; every INSTANCE references a real
   component set and a variant it declares; every spacing/radius token and every style's backing
   colour/type token resolves to a declared variable; variable alias chains resolve with no cycle.
3. **Mapping integrity** — the token and variant mappings key exactly onto the model's nodes: a
   node with bindings has a matching token-mapping entry, and every INSTANCE has a variant-mapping
   entry consistent with its instance ref.
4. **Structure integrity** — each page tree is a valid acyclic rooted tree, the five graphs are
   acyclic where required (enforced by the respective models), and variable collections satisfy
   mode parity (enforced by the collection model).

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–17.

Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied by the
caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from figma_design.domain.component.component_set import ComponentSetCatalog
from figma_design.domain.context.context import SourceRefs
from figma_design.domain.evidence.evidence import EvidenceGraph
from figma_design.domain.graph.graphs import FigmaGraphs
from figma_design.domain.mapping.token_mapping import TokenMapping
from figma_design.domain.mapping.variant_mapping import VariantMapping
from figma_design.domain.node.node import FigmaNode
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.quality.quality import FigmaModelQualityMetrics
from figma_design.domain.shared.ids import (
    FDEvidenceId,
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
    FigmaNodeId,
)
from figma_design.domain.shared.value_objects import FigmaPageKind, NodeType
from figma_design.domain.style.style import StyleSet
from figma_design.domain.variable.collection import VariableCollection
from figma_design.domain.variable.variable import Variable

__all__ = ["FigmaDesignModel", "InvalidFigmaModelError"]


class InvalidFigmaModelError(DesignDirectorError):
    """Raised when a Figma design model violates an integrity invariant."""

    code = "invalid_figma_design_model"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FigmaDesignModel:
    """The complete, provenance-tracked, versioned Figma design model."""

    id: FigmaDesignModelId
    lineage_id: FigmaDesignModelLineageId
    version: int
    project_id: str
    source_refs: SourceRefs
    pages: tuple[FigmaPage, ...]
    collections: tuple[VariableCollection, ...]
    style_set: StyleSet
    component_sets: ComponentSetCatalog
    token_mapping: TokenMapping
    variant_mapping: VariantMapping
    graphs: FigmaGraphs
    evidence_graph: EvidenceGraph
    quality: FigmaModelQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidFigmaModelError(
                "FigmaDesignModel.version must be >= 1.", details={"version": self.version}
            )
        object.__setattr__(self, "pages", tuple(self.pages))
        object.__setattr__(self, "collections", tuple(self.collections))
        if not self.pages:
            raise InvalidFigmaModelError("A FigmaDesignModel must have at least one page.")
        self._validate_provenance()
        self._validate_reference_integrity()
        self._validate_mapping_integrity()

    # -- indices ----------------------------------------------------------- #
    def _all_nodes(self) -> tuple[FigmaNode, ...]:
        return tuple(node for page in self.pages for node in page.tree)

    def _variable_index(self) -> dict[str, Variable]:
        index: dict[str, Variable] = {}
        for collection in self.collections:
            for variable in collection:
                if variable.key in index:
                    raise InvalidFigmaModelError(
                        "A variable key is declared in more than one collection.",
                        details={"key": variable.key},
                    )
                index[variable.key] = variable
        return index

    # -- invariant 1: provenance ------------------------------------------- #
    def _referenced_evidence(self) -> set[FDEvidenceId]:
        referenced: set[FDEvidenceId] = set()
        for page in self.pages:
            referenced.update(page.evidence_ids)
        for component_set in self.component_sets:
            referenced.update(component_set.evidence_ids)
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidFigmaModelError(
                "Model references evidence absent from its evidence graph "
                "(no ungrounded elements).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- invariant 2: reference integrity ---------------------------------- #
    def _require_variable(self, index: dict[str, Variable], key: str, context: str) -> Variable:
        variable = index.get(key)
        if variable is None:
            raise InvalidFigmaModelError(
                f"{context} references variable {key!r} absent from every collection.",
                details={"key": key, "context": context},
            )
        return variable

    def _validate_reference_integrity(self) -> None:
        index = self._variable_index()
        self._assert_no_alias_cycle(index)

        for node in self._all_nodes():
            for binding in node.variable_bindings:
                variable = self._require_variable(
                    index, binding.variable_key, f"node {node.name!r}"
                )
                if not variable.permits(binding.required_scope):
                    raise InvalidFigmaModelError(
                        "A variable binding targets a variable whose scope forbids the property.",
                        details={
                            "node": str(node.id),
                            "property": binding.property,
                            "variable": binding.variable_key,
                        },
                    )
            for token in node.spacing_token_keys:
                self._require_variable(index, token, f"node {node.name!r} geometry")
            for style_ref in (node.fill_style_ref, node.effect_style_ref):
                if style_ref is not None and not self.style_set.has(style_ref):
                    raise InvalidFigmaModelError(
                        "A node references a style absent from the style set.",
                        details={"node": str(node.id), "style": str(style_ref)},
                    )
            if node.type is NodeType.INSTANCE:
                self._validate_instance(node)

        for style in self.style_set:
            for token in style.token_keys:
                self._require_variable(index, token, f"style {style.name!r}")

    def _validate_instance(self, node: FigmaNode) -> None:
        ref = node.instance_ref
        assert ref is not None
        component_set = self.component_sets.by_id(ref.component_set_id)
        if component_set is None:
            raise InvalidFigmaModelError(
                "An instance references a component set not in the catalog.",
                details={"node": str(node.id)},
            )
        if not component_set.declares_variant(ref.variant_name):
            raise InvalidFigmaModelError(
                "An instance selects a variant the component set does not declare.",
                details={"node": str(node.id), "variant": ref.variant_name},
            )
        for prop in ref.property_overrides:
            if prop not in component_set.property_names:
                raise InvalidFigmaModelError(
                    "An instance overrides a property the component set does not declare.",
                    details={"node": str(node.id), "property": prop},
                )

    def _assert_no_alias_cycle(self, index: dict[str, Variable]) -> None:
        adjacency: dict[str, list[str]] = {k: [] for k in index}
        for key, variable in index.items():
            for ref in variable.alias_refs:
                self._require_variable(index, ref, f"variable {key!r}")
                adjacency[key].append(ref)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(adjacency, WHITE)

        def visit(key: str) -> None:
            colour[key] = GREY
            for nxt in adjacency.get(key, ()):
                if colour.get(nxt) == GREY:
                    raise InvalidFigmaModelError(
                        "Variable alias chain forms a cycle.", details={"key": nxt}
                    )
                if colour.get(nxt) == WHITE:
                    visit(nxt)
            colour[key] = BLACK

        for key in adjacency:
            if colour[key] == WHITE:
                visit(key)

    # -- invariant 3: mapping integrity ------------------------------------ #
    def _validate_mapping_integrity(self) -> None:
        node_ids = {node.id for node in self._all_nodes()}
        node_index = {node.id: node for node in self._all_nodes()}

        for node_id, _ in self.token_mapping:
            if node_id not in node_ids:
                raise InvalidFigmaModelError(
                    "Token mapping references a node not in the model.",
                    details={"node": str(node_id)},
                )
        for node_id, _ in self.variant_mapping:
            if node_id not in node_ids:
                raise InvalidFigmaModelError(
                    "Variant mapping references a node not in the model.",
                    details={"node": str(node_id)},
                )

        for node in self._all_nodes():
            expected = {b.variable_key for b in node.variable_bindings}
            if expected and set(self.token_mapping.for_node(node.id)) != expected:
                raise InvalidFigmaModelError(
                    "A node's token mapping does not match its bindings.",
                    details={"node": str(node.id)},
                )
            if node.type is NodeType.INSTANCE:
                selection = self.variant_mapping.for_node(node.id)
                if selection is None:
                    raise InvalidFigmaModelError(
                        "An instance has no variant-mapping entry.",
                        details={"node": str(node.id)},
                    )
                component_set = self.component_sets.by_id(node.instance_ref.component_set_id)
                if component_set is None or selection.component_set_key != component_set.key:
                    raise InvalidFigmaModelError(
                        "An instance's variant mapping names a different component set.",
                        details={"node": str(node.id)},
                    )
                if selection.variant_name != node.instance_ref.variant_name:
                    raise InvalidFigmaModelError(
                        "An instance's variant mapping names a different variant.",
                        details={"node": str(node.id)},
                    )
        # touch the index to keep the intent explicit (nodes resolved above)
        _ = node_index

    # -- queries ----------------------------------------------------------- #
    def page_count(self) -> int:
        return len(self.pages)

    def node_count(self) -> int:
        return sum(page.node_count for page in self.pages)

    def component_set_count(self) -> int:
        return len(self.component_sets)

    def variable_count(self) -> int:
        return sum(len(c) for c in self.collections)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    def pages_of_kind(self, kind: FigmaPageKind) -> tuple[FigmaPage, ...]:
        return tuple(p for p in self.pages if p.kind is kind)

    @property
    def is_production_ready(self) -> bool:
        """Whether the model is complete enough to render a Figma file.

        Requires pages and nodes, a design-system page, at least one component set and variable
        collection, full grounding and reference integrity, and non-empty evidence — the
        structural invariants are already guaranteed at construction.
        """
        if not self.pages or self.node_count() == 0:
            return False
        return (
            bool(self.pages_of_kind(FigmaPageKind.DESIGN_SYSTEM))
            and self.component_set_count() >= 1
            and len(self.collections) >= 1
            and self.quality.is_fully_grounded
            and self.quality.has_reference_integrity
            and self.evidence_count() > 0
        )
