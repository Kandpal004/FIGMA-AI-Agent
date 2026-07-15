"""ComponentCompositionSpecification — the aggregate the whole engine produces.

An immutable, versioned specification: the component composition (the per-component decisions),
the compatibility web, the composition/placement/visibility/responsive/reuse rules, the two
graphs, the quality picture. It is the brain behind every future component — the authoritative
answer to which components should exist, why, where, and when not.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any decision, compatibility link,
   rule, or graph node must resolve in the specification's :class:`EvidenceGraph`. No component
   the engine cannot cite can be built — a component never enters the composition at random.
2. **Coherence integrity** — the engine's spine: every dependency (and ``REQUIRES`` target) of
   an included component is itself included (dependency closure), and no two components that
   ``CONFLICT`` are both included *and* placed on the same page (the "which components cannot
   exist together" rule, made structural). Every placement targets an included component.
3. **Graph integrity** — both graphs are acyclic and resolve (enforced by the graph primitive).

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–14.

Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from component_intelligence.domain.compatibility.compatibility import CompatibilitySet
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.evidence.evidence import EvidenceGraph
from component_intelligence.domain.graph.graphs import ComponentGraphs
from component_intelligence.domain.quality.quality import CompositionQualityMetrics
from component_intelligence.domain.rules.composition_rules import CompositionRuleSet
from component_intelligence.domain.rules.placement_rules import PlacementRuleSet
from component_intelligence.domain.rules.responsive_rules import ResponsiveRuleSet
from component_intelligence.domain.rules.reuse_rules import ReuseRuleSet
from component_intelligence.domain.rules.visibility_rules import VisibilityRuleSet
from component_intelligence.domain.shared.ids import (
    CIEvidenceId,
    ComponentSpecId,
    ComponentSpecLineageId,
)
from component_intelligence.domain.shared.value_objects import ComponentType

__all__ = ["ComponentCompositionSpecification", "InvalidSpecificationError"]


class InvalidSpecificationError(DesignDirectorError):
    """Raised when a specification violates an integrity invariant."""

    code = "invalid_component_intelligence_specification"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentCompositionSpecification:
    """The complete, provenance-tracked, versioned component-composition specification."""

    id: ComponentSpecId
    lineage_id: ComponentSpecLineageId
    version: int
    project_id: str
    composition: ComponentComposition
    compatibility: CompatibilitySet
    composition_rules: CompositionRuleSet
    placement_rules: PlacementRuleSet
    visibility_rules: VisibilityRuleSet
    responsive_rules: ResponsiveRuleSet
    reuse_rules: ReuseRuleSet
    graphs: ComponentGraphs
    evidence_graph: EvidenceGraph
    quality: CompositionQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidSpecificationError(
                "ComponentCompositionSpecification.version must be >= 1.",
                details={"version": self.version},
            )
        self._validate_provenance()
        self._validate_coherence()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[CIEvidenceId]:
        referenced: set[CIEvidenceId] = set()
        referenced.update(self.composition.evidence_ids())
        referenced.update(self.compatibility.evidence_ids())
        referenced.update(self.composition_rules.evidence_ids())
        referenced.update(self.placement_rules.evidence_ids())
        referenced.update(self.visibility_rules.evidence_ids())
        referenced.update(self.responsive_rules.evidence_ids())
        referenced.update(self.reuse_rules.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidSpecificationError(
                "Specification references evidence absent from its evidence graph "
                "(no ungrounded component decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def conflict_pairs(self) -> set[frozenset[ComponentType]]:
        """Every unordered pair of components declared to conflict."""
        pairs: set[frozenset[ComponentType]] = set()
        for link in self.compatibility.conflicts():
            pairs.add(frozenset({link.source, link.target}))
        for decision in self.composition:
            for other in decision.usage.conflicts_with:
                pairs.add(frozenset({decision.component, other}))
        return pairs

    def _validate_coherence(self) -> None:
        included = self.composition.included_components()

        # Dependency closure: every dependency / required component is included.
        for decision in self.composition.included():
            missing = [d.value for d in decision.dependencies if d not in included]
            if missing:
                raise InvalidSpecificationError(
                    "An included component depends on components not in the composition.",
                    details={"component": decision.component.value, "missing": missing},
                )
        for component in included:
            for required in self.compatibility.requires_of(component):
                if required not in included:
                    raise InvalidSpecificationError(
                        "An included component requires a component not in the composition.",
                        details={"component": component.value, "requires": required.value},
                    )

        # Placement targets must be included.
        for rule in self.placement_rules:
            if rule.component not in included:
                raise InvalidSpecificationError(
                    "A placement rule targets a component that is not included.",
                    details={"component": rule.component.value},
                )

        # No two conflicting components may be co-placed on the same page.
        for page in self.placement_rules.pages():
            on_page = self.placement_rules.components_on(page)
            for pair in self.conflict_pairs():
                if pair <= on_page:
                    a, b = sorted(c.value for c in pair)
                    raise InvalidSpecificationError(
                        "Two conflicting components are placed on the same page.",
                        details={"page": page.value, "components": [a, b]},
                    )

    # -- queries ----------------------------------------------------------- #
    def component_count(self) -> int:
        return len(self.composition)

    def included_count(self) -> int:
        return len(self.composition.included())

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_production_ready(self) -> bool:
        """Whether the composition is complete enough to build components from.

        Requires every included component fully specified, full grounding, at least one
        placement rule, and non-empty evidence — coherence is already guaranteed at
        construction.
        """
        included = self.composition.included()
        if not included:
            return False
        return (
            all(d.is_fully_specified for d in included)
            and self.quality.is_fully_grounded
            and len(self.placement_rules) >= 1
            and self.evidence_count() > 0
        )
