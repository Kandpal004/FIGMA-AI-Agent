"""The FigmaDesignBundle — the neutral hand-off a future renderer / MCP adapter consumes.

The Figma Design Engine is renderer-independent: it imports nothing from any later phase and no
Figma SDK, MCP client, or HTTP library. Instead it emits this neutral, self-contained bundle — the
organized pages and their layer trees, the variable collections and modes, the published styles,
the component-set catalog, and the resolved token/variant mappings — everything a downstream Figma
renderer (or a future React/HTML/Shopify/Magento renderer) needs to *materialise* the file, and
nothing that pre-empts how. A future Phase-19 renderer consumes it through a port *it* owns.

Pure domain: standard library and the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from figma_design.domain.component.component_set import ComponentSetCatalog
from figma_design.domain.context.context import SourceRefs
from figma_design.domain.mapping.token_mapping import TokenMapping
from figma_design.domain.mapping.variant_mapping import VariantMapping
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.shared.ids import FigmaDesignModelId
from figma_design.domain.style.style import StyleSet
from figma_design.domain.variable.collection import VariableCollection

__all__ = ["FigmaDesignBundle"]


@dataclass(frozen=True, slots=True)
class FigmaDesignBundle:
    """The neutral Figma design model a downstream renderer builds from.

    Attributes:
        model_id: The model version this bundle projects.
        project_id: The owning project.
        source_refs: The upstream artifacts the model was built from.
        pages: The organized pages and their layer trees.
        collections: The variable collections (with modes).
        style_set: The published styles.
        component_sets: The component-set catalog.
        token_mapping: The resolved variable bindings per node.
        variant_mapping: The resolved variant selections per instance.
        is_production_ready: Whether the model is settled.
        created_at: When the model was produced.
    """

    model_id: FigmaDesignModelId
    project_id: str
    source_refs: SourceRefs
    pages: tuple[FigmaPage, ...]
    collections: tuple[VariableCollection, ...]
    style_set: StyleSet
    component_sets: ComponentSetCatalog
    token_mapping: TokenMapping
    variant_mapping: VariantMapping
    is_production_ready: bool
    created_at: datetime

    @classmethod
    def from_model(cls, model: FigmaDesignModel) -> FigmaDesignBundle:
        return cls(
            model_id=model.id,
            project_id=model.project_id,
            source_refs=model.source_refs,
            pages=model.pages,
            collections=model.collections,
            style_set=model.style_set,
            component_sets=model.component_sets,
            token_mapping=model.token_mapping,
            variant_mapping=model.variant_mapping,
            is_production_ready=model.is_production_ready,
            created_at=model.created_at,
        )
