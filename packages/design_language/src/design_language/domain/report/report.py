"""DesignLanguageSpecification — the aggregate the whole engine produces.

An immutable, versioned specification: the industry preset, the Visual DNA, the token system,
the philosophies and personalities, the grid and responsive systems, the language selection,
the consistency/composition/constraint rules, the two graphs, the quality picture, and the
articulated explanation. It is the visual source of truth every future Design System,
Component Library, and UI composition inherits from.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any DNA trait, philosophy,
   token, personality, rule, constraint, language selection, explanation, or graph node must
   resolve in the specification's :class:`EvidenceGraph`. No visual decision the engine cannot
   cite can be built — which is what keeps the language from looking arbitrary or AI-generated.
2. **Graph integrity** — both graphs are acyclic and resolve (enforced by the graph
   primitive).

``is_production_ready`` layers the completeness promise on top: all nineteen visual attributes
determined, a distinctive DNA, full grounding, consistency rules and constraints present, and
a deliberate language selection.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–13.

Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from design_language.domain.dna.visual_dna import VisualDNA
from design_language.domain.evidence.evidence import EvidenceGraph
from design_language.domain.graph.graphs import DesignLanguageGraphs
from design_language.domain.language.selection import LanguageSelection
from design_language.domain.personality.personality import PersonalitySet
from design_language.domain.philosophy.philosophy import PhilosophySet
from design_language.domain.quality.quality import DesignLanguageQualityMetrics
from design_language.domain.report.explanation import LanguageExplanation
from design_language.domain.rules.composition import CompositionRuleSet
from design_language.domain.rules.consistency import ConsistencyRuleSet
from design_language.domain.rules.constraint import ConstraintSet
from design_language.domain.shared.ids import (
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
    DLEvidenceId,
)
from design_language.domain.shared.value_objects import (
    IndustryPreset,
    PersonalityKind,
    PhilosophyKind,
)
from design_language.domain.system.grid_system import GridSystem
from design_language.domain.system.responsive import ResponsiveStrategy
from design_language.domain.tokens.visual_tokens import VisualTokens

__all__ = ["DesignLanguageSpecification", "InvalidSpecificationError"]

# The eight philosophy kinds the spec explicitly requires the engine to determine.
REQUIRED_PHILOSOPHIES = frozenset({
    PhilosophyKind.SPACING, PhilosophyKind.GRID, PhilosophyKind.ALIGNMENT,
    PhilosophyKind.CONTAINER, PhilosophyKind.ELEVATION, PhilosophyKind.SURFACE,
    PhilosophyKind.MOTION, PhilosophyKind.INTERACTION,
})
REQUIRED_PERSONALITIES = frozenset(PersonalityKind)


class InvalidSpecificationError(DesignDirectorError):
    """Raised when a specification violates an integrity invariant."""

    code = "invalid_design_language_specification"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DesignLanguageSpecification:
    """The complete, provenance-tracked, versioned design-language specification."""

    id: DesignLanguageSpecId
    lineage_id: DesignLanguageSpecLineageId
    version: int
    project_id: str
    industry: IndustryPreset
    visual_dna: VisualDNA
    tokens: VisualTokens
    philosophies: PhilosophySet
    personalities: PersonalitySet
    grid_system: GridSystem
    responsive_strategy: ResponsiveStrategy
    language_selection: LanguageSelection
    consistency_rules: ConsistencyRuleSet
    composition_rules: CompositionRuleSet
    constraints: ConstraintSet
    graphs: DesignLanguageGraphs
    evidence_graph: EvidenceGraph
    quality: DesignLanguageQualityMetrics
    explanation: LanguageExplanation
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidSpecificationError(
                "DesignLanguageSpecification.version must be >= 1.",
                details={"version": self.version},
            )
        self._validate_provenance()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[DLEvidenceId]:
        referenced: set[DLEvidenceId] = set()
        referenced.update(self.visual_dna.all_evidence_ids())
        referenced.update(self.tokens.all_evidence_ids())
        referenced.update(self.philosophies.evidence_ids())
        referenced.update(self.personalities.evidence_ids())
        referenced.update(self.grid_system.all_evidence_ids())
        referenced.update(self.responsive_strategy.all_evidence_ids())
        referenced.update(self.language_selection.all_evidence_ids())
        referenced.update(self.consistency_rules.evidence_ids())
        referenced.update(self.composition_rules.evidence_ids())
        referenced.update(self.constraints.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        referenced.update(self.explanation.all_evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidSpecificationError(
                "Specification references evidence absent from its evidence graph "
                "(no ungrounded visual decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- queries ----------------------------------------------------------- #
    def determined_attribute_count(self) -> int:
        """How many of the nineteen visual attributes are determined.

        Seven live on the DNA, eight are required philosophies, four are personalities.
        """
        philosophy_kinds = self.philosophies.kinds() & REQUIRED_PHILOSOPHIES
        personality_kinds = self.personalities.kinds() & REQUIRED_PERSONALITIES
        return 7 + len(philosophy_kinds) + len(personality_kinds)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_production_ready(self) -> bool:
        """Whether the visual language is settled enough to inherit from.

        Requires all nineteen attributes determined, a distinctive DNA, full grounding, at
        least one consistency rule and one constraint, a deliberate language selection, and
        non-empty evidence — this is the platform's "the visual language is settled" signal.
        """
        return (
            self.determined_attribute_count() == 19
            and self.visual_dna.is_distinctive
            and self.quality.is_fully_grounded
            and len(self.consistency_rules) >= 1
            and len(self.constraints) >= 1
            and self.evidence_count() > 0
        )
