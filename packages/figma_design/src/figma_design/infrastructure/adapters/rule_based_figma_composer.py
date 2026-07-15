"""The deterministic, rule-based Figma Composer — the default file-craft brain.

Implements :class:`FigmaComposerPort` without any LLM: it turns the codified
:mod:`~figma_design.infrastructure.adapters.figma_baseline` rulebook into cited domain pages,
variable collections, styles, and component sets, adapting to the brief (which device frames to
render) and grounding every node and component set in the consolidated evidence. It is fully
deterministic — the same input and evidence always yield the same file — so the model is
reproducible and auditable.

It structures the file the way a senior designer does: a Cover page, a Design System page
(variables + styles), a Components page (component sets and their variants), and one page per
storefront page with a device frame per device class, each holding auto-layout section frames that
instance the right component and variant. It cites, never invents — every node references real
evidence ids drawn from the graph, spread across the six upstream provenances — and it references
only declared variables, styles, and component sets. It imports no Figma SDK, MCP client, or HTTP
library.

Pure infrastructure: the baseline data, the domain models, and the application contracts/ports.
"""

from __future__ import annotations

from figma_design.application.contracts import FigmaDraft, FigmaInput
from figma_design.application.ports.figma_composer import FigmaComposerPort
from figma_design.domain.component.component import FigmaComponent, VariantDefinition
from figma_design.domain.component.component_set import ComponentSetCatalog, FigmaComponentSet
from figma_design.domain.component.property import ComponentProperty
from figma_design.domain.evidence.evidence import Citation, EvidenceGraph, FDEvidence
from figma_design.domain.geometry.geometry import CornerRadius, Padding, Size
from figma_design.domain.layout.auto_layout import AutoLayout
from figma_design.domain.node.content import InstanceRef, TextContent
from figma_design.domain.node.node import FigmaNode, FigmaTree
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.shared.ids import (
    FigmaComponentId,
    FigmaComponentSetId,
    FigmaNodeId,
    FigmaPageId,
    StyleId,
    VariableCollectionId,
    VariableId,
)
from figma_design.domain.shared.value_objects import (
    AxisAlign,
    ComponentPropertyType,
    DeviceClass,
    EffectType,
    FigmaPageKind,
    LayoutMode,
    NodeType,
    PaintType,
    ProvenanceKind,
    SizingMode,
    StyleType,
)
from figma_design.domain.style.paint import Effect, Paint
from figma_design.domain.style.style import Style, StyleSet
from figma_design.domain.style.typography import TypographyStyle
from figma_design.domain.variable.binding import VariableBinding
from figma_design.domain.variable.collection import VariableCollection
from figma_design.domain.variable.variable import Variable, VariableValue
from figma_design.infrastructure.adapters import figma_baseline as bl

__all__ = ["RuleBasedFigmaComposer"]

_PROVENANCE_CYCLE = (
    ProvenanceKind.DESIGN_ORCHESTRATOR,
    ProvenanceKind.DESIGN_SYSTEM,
    ProvenanceKind.COMPONENT_INTELLIGENCE,
    ProvenanceKind.DESIGN_LANGUAGE,
    ProvenanceKind.CREATIVE_DIRECTOR,
    ProvenanceKind.KNOWLEDGE,
)

_DEVICE_NAME = {
    DeviceClass.DESKTOP: "Desktop",
    DeviceClass.TABLET: "Tablet",
    DeviceClass.MOBILE: "Mobile",
    DeviceClass.ADAPTIVE: "Adaptive",
}


class _CiteSource:
    """Picks real evidence, preferring given provenances, falling back to any."""

    def __init__(self, evidence: EvidenceGraph) -> None:
        self._by_prov: dict[ProvenanceKind, list[FDEvidence]] = {}
        for item in evidence:
            self._by_prov.setdefault(item.provenance, []).append(item)
        self._any: list[FDEvidence] = list(evidence)
        self._counter = 0

    def next(self) -> tuple[Citation, ...]:
        provenance = _PROVENANCE_CYCLE[self._counter % len(_PROVENANCE_CYCLE)]
        self._counter += 1
        bucket = self._by_prov.get(provenance)
        if bucket:
            return (Citation(evidence_id=bucket[0].id, relevance="grounds this element"),)
        if self._any:
            return (Citation(evidence_id=self._any[0].id, relevance="grounds this element"),)
        return ()


class RuleBasedFigmaComposer(FigmaComposerPort):
    """A deterministic composer that grounds the codified file rulebook in evidence."""

    async def compose(
        self, figma_input: FigmaInput, evidence: EvidenceGraph
    ) -> FigmaDraft:
        cite = _CiteSource(evidence)
        collections = self._build_collections()
        style_set, style_ids = self._build_styles()
        component_sets = self._build_component_sets(cite)

        pages: list[FigmaPage] = []
        order = 1
        pages.append(self._cover_page(order, cite))
        order += 1
        pages.append(self._design_system_page(order, style_ids, cite))
        order += 1
        pages.append(self._components_page(order, component_sets, cite))
        order += 1
        for spec in bl.STOREFRONT_PAGES:
            pages.append(
                self._storefront_page(order, spec, component_sets, figma_input.brief, cite)
            )
            order += 1

        return FigmaDraft(
            pages=tuple(pages),
            collections=collections,
            style_set=style_set,
            component_sets=component_sets,
        )

    # -- variables --------------------------------------------------------- #
    def _build_collections(self) -> tuple[VariableCollection, ...]:
        collections: list[VariableCollection] = []
        for spec in bl.COLLECTIONS:
            variables = [
                Variable(
                    id=VariableId.new(),
                    key=vs.key,
                    type=vs.type,
                    scopes=frozenset(vs.scopes),
                    values={
                        mode: (
                            VariableValue.of(payload)
                            if kind == "lit"
                            else VariableValue.alias(payload)
                        )
                        for mode, (kind, payload) in vs.values.items()
                    },
                )
                for vs in spec.variables
            ]
            collections.append(
                VariableCollection.of(
                    VariableCollectionId.new(), spec.kind, spec.name, spec.modes, variables
                )
            )
        return tuple(collections)

    # -- styles ------------------------------------------------------------ #
    def _build_styles(self) -> tuple[StyleSet, dict[str, StyleId]]:
        styles: list[Style] = []
        ids: dict[str, StyleId] = {}
        for spec in bl.STYLES:
            style_id = StyleId.new()
            ids[spec.name] = style_id
            if spec.type is StyleType.FILL:
                styles.append(Style(
                    id=style_id, name=spec.name, type=StyleType.FILL,
                    paints=(Paint(type=PaintType.SOLID, color_token=spec.color_token),),
                ))
            elif spec.type is StyleType.TEXT:
                styles.append(Style(
                    id=style_id, name=spec.name, type=StyleType.TEXT,
                    typography=TypographyStyle(
                        font_family=spec.font_family, font_weight=spec.font_weight,
                        font_size_token=spec.font_size_token, line_height=spec.line_height,
                    ),
                ))
            elif spec.type is StyleType.EFFECT:
                styles.append(Style(
                    id=style_id, name=spec.name, type=StyleType.EFFECT,
                    effects=(Effect(
                        type=EffectType.DROP_SHADOW, radius=spec.effect_radius,
                        color_token=spec.color_token, offset_y=spec.effect_offset_y,
                    ),),
                ))
            else:
                styles.append(Style(
                    id=style_id, name=spec.name, type=StyleType.GRID,
                    grid_columns=spec.grid_columns,
                ))
        return StyleSet.of(styles), ids

    # -- component sets ---------------------------------------------------- #
    def _build_component_sets(self, cite: _CiteSource) -> ComponentSetCatalog:
        sets: list[FigmaComponentSet] = []
        for spec in bl.COMPONENT_SETS:
            properties = [
                ComponentProperty(
                    name="variant", type=ComponentPropertyType.VARIANT,
                    options=spec.variants, default=spec.variants[0],
                )
            ]
            for boolean in spec.boolean_props:
                properties.append(
                    ComponentProperty(name=boolean, type=ComponentPropertyType.BOOLEAN)
                )
            components = [
                FigmaComponent(
                    id=FigmaComponentId.new(),
                    variant=VariantDefinition(variant, {"variant": variant}),
                )
                for variant in spec.variants
            ]
            sets.append(FigmaComponentSet(
                id=FigmaComponentSetId.new(), key=spec.key, name=spec.name,
                properties=tuple(properties), components=tuple(components), citations=cite.next(),
            ))
        return ComponentSetCatalog.of(sets)

    # -- pages ------------------------------------------------------------- #
    def _cover_page(self, order: int, cite: _CiteSource) -> FigmaPage:
        root = FigmaNode(
            id=FigmaNodeId.new(), type=NodeType.FRAME, name="Cover",
            auto_layout=AutoLayout(
                mode=LayoutMode.VERTICAL, primary_align=AxisAlign.CENTER,
                counter_align=AxisAlign.CENTER, item_spacing_token="space.4",
                padding=Padding.uniform("space.16"),
            ),
            width=Size.fixed(1440), height=Size.fixed(1024),
            citations=cite.next(),
        )
        title = FigmaNode(
            id=FigmaNodeId.new(), type=NodeType.TEXT, name="Title", parent_id=root.id,
            text_content=TextContent("Storefront Design System"), citations=cite.next(),
        )
        return FigmaPage(
            id=FigmaPageId.new(), kind=FigmaPageKind.COVER, name="📕 Cover", order=order,
            tree=FigmaTree.of([root, title]),
        )

    def _design_system_page(
        self, order: int, style_ids: dict[str, StyleId], cite: _CiteSource
    ) -> FigmaPage:
        root = FigmaNode(
            id=FigmaNodeId.new(), type=NodeType.FRAME, name="Design System",
            auto_layout=AutoLayout(
                mode=LayoutMode.VERTICAL, item_spacing_token="space.8",
                padding=Padding.uniform("space.12"),
            ),
            width=Size.fixed(1440),
            corner_radius=CornerRadius("radius.lg"),
            variable_bindings=(VariableBinding("fill", "color.bg.default"),),
            citations=cite.next(),
        )
        nodes = [root]
        for label, style_name in (
            ("Colors", "Surface/Default"),
            ("Typography", "Heading/H1"),
            ("Effects", "Shadow/MD"),
        ):
            nodes.append(FigmaNode(
                id=FigmaNodeId.new(), type=NodeType.FRAME, name=label, parent_id=root.id,
                width=Size.fill(),
                auto_layout=AutoLayout(mode=LayoutMode.HORIZONTAL, item_spacing_token="space.4",
                                       padding=Padding.uniform("space.6")),
                fill_style_ref=style_ids[style_name], citations=cite.next(),
            ))
        return FigmaPage(
            id=FigmaPageId.new(), kind=FigmaPageKind.DESIGN_SYSTEM, name="🎨 Design System",
            order=order, tree=FigmaTree.of(nodes),
        )

    def _components_page(
        self, order: int, catalog: ComponentSetCatalog, cite: _CiteSource
    ) -> FigmaPage:
        root = FigmaNode(
            id=FigmaNodeId.new(), type=NodeType.SECTION, name="Components",
            auto_layout=AutoLayout(mode=LayoutMode.WRAP, wrap=True, item_spacing_token="space.8",
                                   padding=Padding.uniform("space.8")),
            width=Size.fixed(1440), citations=cite.next(),
        )
        nodes = [root]
        for component_set in catalog:
            set_node = FigmaNode(
                id=FigmaNodeId.new(), type=NodeType.COMPONENT_SET, name=component_set.name,
                parent_id=root.id, citations=cite.next(),
            )
            nodes.append(set_node)
            for component in component_set.components:
                nodes.append(FigmaNode(
                    id=FigmaNodeId.new(), type=NodeType.COMPONENT,
                    name=f"{component_set.key}={component.name}", parent_id=set_node.id,
                    citations=cite.next(),
                ))
        return FigmaPage(
            id=FigmaPageId.new(), kind=FigmaPageKind.COMPONENTS, name="🧩 Components",
            order=order, tree=FigmaTree.of(nodes),
        )

    def _storefront_page(
        self, order: int, spec, catalog: ComponentSetCatalog, brief, cite: _CiteSource
    ) -> FigmaPage:
        root = FigmaNode(
            id=FigmaNodeId.new(), type=NodeType.SECTION, name=spec.name,
            auto_layout=AutoLayout(mode=LayoutMode.HORIZONTAL, item_spacing_token="space.16",
                                   padding=Padding.uniform("space.8")),
            citations=cite.next(),
        )
        nodes = [root]
        for device in brief.devices:
            device_frame = FigmaNode(
                id=FigmaNodeId.new(), type=NodeType.FRAME,
                name=f"{spec.name} / {_DEVICE_NAME[device]}", parent_id=root.id,
                auto_layout=AutoLayout(mode=LayoutMode.VERTICAL, item_spacing_token="space.6",
                                       padding=Padding.uniform("space.4")),
                width=Size.fixed(self._device_width(device)),
                citations=cite.next(),
            )
            nodes.append(device_frame)
            for section in spec.sections:
                component_set = catalog.get(section.component_key)
                section_frame = FigmaNode(
                    id=FigmaNodeId.new(), type=NodeType.FRAME,
                    name=f"Section / {section.section}", parent_id=device_frame.id,
                    width=Size.fill(),
                    auto_layout=AutoLayout(mode=LayoutMode.VERTICAL,
                                           primary_axis_sizing=SizingMode.HUG,
                                           counter_axis_sizing=SizingMode.FILL,
                                           item_spacing_token="space.4",
                                           padding=Padding.symmetric("space.6", "space.8")),
                    corner_radius=CornerRadius("radius.md"),
                    variable_bindings=(VariableBinding("fill", "color.bg.default"),),
                    citations=cite.next(),
                )
                nodes.append(section_frame)
                nodes.append(FigmaNode(
                    id=FigmaNodeId.new(), type=NodeType.INSTANCE, name=component_set.name,
                    parent_id=section_frame.id, width=Size.fill(),
                    instance_ref=InstanceRef(
                        component_set_id=component_set.id, variant_name=section.variant
                    ),
                    citations=cite.next(),
                ))
        return FigmaPage(
            id=FigmaPageId.new(), kind=FigmaPageKind.PAGE, name=f"📄 {spec.name}",
            order=order, tree=FigmaTree.of(nodes),
        )

    @staticmethod
    def _device_width(device: DeviceClass) -> float:
        return {
            DeviceClass.DESKTOP: 1440,
            DeviceClass.TABLET: 768,
            DeviceClass.MOBILE: 390,
            DeviceClass.ADAPTIVE: 1200,
        }[device]
