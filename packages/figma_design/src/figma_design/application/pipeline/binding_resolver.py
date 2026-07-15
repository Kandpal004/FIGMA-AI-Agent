"""Stage — Binding Resolution (the "no fabrication" gate).

Before the model is assembled, this stage freezes the composer's bindings into the resolved
:class:`TokenMapping` and :class:`VariantMapping`, and integrity-checks every reference against
the declared variable collections, styles, and component sets: each variable binding must target a
declared variable whose scope permits the property; each spacing/radius token and each style's
backing colour/type token must resolve to a variable; each instance must reference a real component
set and a variant it declares. A reference that dangles — the tell-tale of an invented value — is
rejected with :class:`UnresolvableReferenceError`.

Because the deterministic composer only ever references declared variables, styles, and component
sets, this resolver returns full reference integrity for a well-formed draft; it exists to make
"the engine only references what the design system declared" a gate, not a hope.
"""

from __future__ import annotations

from core.errors import DesignDirectorError

from figma_design.application.contracts import FigmaDraft
from figma_design.domain.mapping.token_mapping import TokenMapping
from figma_design.domain.mapping.variant_mapping import InstanceSelection, VariantMapping
from figma_design.domain.shared.value_objects import NodeType, Percentage
from figma_design.domain.variable.variable import Variable

__all__ = ["ResolvedBindings", "BindingResolver", "UnresolvableReferenceError"]


class UnresolvableReferenceError(DesignDirectorError):
    """Raised when a node references a variable/style/component that is not declared."""

    code = "unresolvable_figma_design_reference"
    http_status = 422


class ResolvedBindings:
    """The frozen result of resolution: the two mappings and the integrity ratio."""

    __slots__ = ("token_mapping", "variant_mapping", "reference_integrity")

    def __init__(
        self,
        token_mapping: TokenMapping,
        variant_mapping: VariantMapping,
        reference_integrity: Percentage,
    ) -> None:
        self.token_mapping = token_mapping
        self.variant_mapping = variant_mapping
        self.reference_integrity = reference_integrity


class BindingResolver:
    """Resolves and integrity-checks every node's variable/style/instance references."""

    def resolve(self, draft: FigmaDraft) -> ResolvedBindings:
        index = self._variable_index(draft)
        token_bindings: dict = {}
        variant_selections: dict = {}

        for node in draft.nodes:
            for binding in node.variable_bindings:
                variable = self._require(index, binding.variable_key, f"node {node.name!r}")
                if not variable.permits(binding.required_scope):
                    raise UnresolvableReferenceError(
                        "A variable binding targets a variable whose scope forbids the property.",
                        details={
                            "node": str(node.id),
                            "property": binding.property,
                            "variable": binding.variable_key,
                        },
                    )
            for token in node.spacing_token_keys:
                self._require(index, token, f"node {node.name!r} geometry")
            for style_ref in (node.fill_style_ref, node.effect_style_ref):
                if style_ref is not None and not draft.style_set.has(style_ref):
                    raise UnresolvableReferenceError(
                        "A node references a style absent from the style set.",
                        details={"node": str(node.id)},
                    )
            if node.variable_bindings:
                token_bindings[node.id] = tuple(
                    b.variable_key for b in node.variable_bindings
                )
            if node.type is NodeType.INSTANCE:
                variant_selections[node.id] = self._resolve_instance(draft, node)

        for style in draft.style_set:
            for token in style.token_keys:
                self._require(index, token, f"style {style.name!r}")

        return ResolvedBindings(
            token_mapping=TokenMapping(token_bindings),
            variant_mapping=VariantMapping(variant_selections),
            reference_integrity=Percentage.of(1.0),
        )

    @staticmethod
    def _variable_index(draft: FigmaDraft) -> dict[str, Variable]:
        index: dict[str, Variable] = {}
        for collection in draft.collections:
            for variable in collection:
                if variable.key in index:
                    raise UnresolvableReferenceError(
                        "A variable key is declared in more than one collection.",
                        details={"key": variable.key},
                    )
                index[variable.key] = variable
        return index

    @staticmethod
    def _require(index: dict[str, Variable], key: str, context: str) -> Variable:
        variable = index.get(key)
        if variable is None:
            raise UnresolvableReferenceError(
                f"{context} references variable {key!r} absent from every collection.",
                details={"key": key, "context": context},
            )
        return variable

    @staticmethod
    def _resolve_instance(draft: FigmaDraft, node) -> InstanceSelection:
        ref = node.instance_ref
        component_set = draft.component_sets.by_id(ref.component_set_id)
        if component_set is None:
            raise UnresolvableReferenceError(
                "An instance references a component set not in the catalog.",
                details={"node": str(node.id)},
            )
        if not component_set.declares_variant(ref.variant_name):
            raise UnresolvableReferenceError(
                "An instance selects a variant the component set does not declare.",
                details={"node": str(node.id), "variant": ref.variant_name},
            )
        return InstanceSelection(
            component_set_key=component_set.key, variant_name=ref.variant_name
        )
