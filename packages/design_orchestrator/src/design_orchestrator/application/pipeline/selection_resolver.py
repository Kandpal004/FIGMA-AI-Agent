"""Stage — Selection Resolution (the "no guessing" gate).

Before the plan is assembled, this stage freezes the planner's choices into the resolved
:class:`TokenMapping` and :class:`VariantMapping`, and integrity-checks each section: every token
a section's layout/spacing/typography/visual/animation choices *reference* must actually be
*bound* by the section, and each section's variant must be a well-formed choice for its
component. A section whose choices reference a token it never binds — the tell-tale of an
invented, unresolvable value — is rejected with :class:`UnresolvableSelectionError`.

Because the deterministic planner only ever chooses from the Design System's declared token keys
and component variants, this resolver returns full binding integrity for a well-formed plan; it
exists to make "the orchestrator only picks what upstream declared" a gate, not a hope.
"""

from __future__ import annotations

from core.errors import DesignDirectorError

from design_orchestrator.application.contracts import ExecutionDraft
from design_orchestrator.domain.mapping.token_mapping import TokenMapping
from design_orchestrator.domain.mapping.variant_mapping import VariantChoice, VariantMapping
from design_orchestrator.domain.shared.value_objects import Percentage

__all__ = ["ResolvedSelection", "SelectionResolver", "UnresolvableSelectionError"]


class UnresolvableSelectionError(DesignDirectorError):
    """Raised when a section references a token it does not bind (an unresolvable selection)."""

    code = "unresolvable_design_orchestrator_selection"
    http_status = 422


class ResolvedSelection:
    """The frozen result of resolution: the two mappings and the integrity ratio."""

    __slots__ = ("token_mapping", "variant_mapping", "binding_integrity")

    def __init__(
        self,
        token_mapping: TokenMapping,
        variant_mapping: VariantMapping,
        binding_integrity: Percentage,
    ) -> None:
        self.token_mapping = token_mapping
        self.variant_mapping = variant_mapping
        self.binding_integrity = binding_integrity


class SelectionResolver:
    """Resolves and integrity-checks each section's token and variant selections."""

    def resolve(self, draft: ExecutionDraft) -> ResolvedSelection:
        token_bindings = {}
        variant_choices = {}
        for section in draft.sections:
            bound = set(section.token_bindings)
            referenced = set(section.choice_token_keys)
            missing = referenced - bound
            if missing:
                raise UnresolvableSelectionError(
                    "A section references tokens it does not bind (unresolvable selection).",
                    details={
                        "section": str(section.id),
                        "component": section.component.value,
                        "missing": sorted(missing),
                    },
                )
            token_bindings[section.id] = section.token_bindings
            variant_choices[section.id] = VariantChoice(
                component=section.component, variant_name=section.variant_name
            )
        return ResolvedSelection(
            token_mapping=TokenMapping(token_bindings),
            variant_mapping=VariantMapping(variant_choices),
            binding_integrity=Percentage.of(1.0),
        )
