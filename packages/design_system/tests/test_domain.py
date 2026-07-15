"""Domain invariant tests — the structural guarantees of the design system.

Proves the anti-randomness and integrity contracts hold at construction: typed identities, the
token literal-xor-reference and tiering rules, dangling-reference and alias-cycle rejection,
theme parity, the mandatory blocking constraints, component platform completeness and variant
integrity, graph acyclicity, and the aggregate's provenance + token-integrity invariants.
"""

from __future__ import annotations

import dataclasses

import pytest

from design_system.domain.component.mapping import PlatformMapping
from design_system.domain.component.spec import (
    AccessibilitySpec,
    ComponentSpec,
    InvalidComponentSpecError,
    PerformanceBudget,
)
from design_system.domain.component.variant import (
    ComponentProperty,
    ComponentStateSpec,
    ComponentVariant,
    ResponsiveSpec,
)
from design_system.domain.constraint.constraint import (
    Constraint,
    ConstraintSet,
    InvalidConstraintError,
)
from design_system.domain.evidence.evidence import Citation, DSEvidence, EvidenceGraph
from design_system.domain.graph.ds_graph import (
    DSEdge,
    DSGraph,
    DSNode,
    InvalidDSGraphError,
)
from design_system.domain.report.report import (
    DesignSystemSpecification,
    InvalidSpecificationError,
)
from design_system.domain.shared.ids import (
    ComponentSpecId,
    ConstraintId,
    DSEdgeId,
    DSEvidenceId,
    DSNodeId,
    DesignSystemSpecId,
    Identifier,
    InvalidDSIdError,
    ThemeId,
    TokenId,
)
from design_system.domain.shared.value_objects import (
    AtomicLevel,
    Breakpoint,
    ComponentType,
    Confidence,
    ConstraintKind,
    Direction,
    EnforcementLevel,
    GraphKind,
    GraphRelation,
    NodeKind,
    Platform,
    PropertyType,
    ProvenanceKind,
    StateKind,
    ThemeMode,
    TokenCategory,
    TokenTier,
)
from design_system.domain.theme.theme import InvalidThemeError, Theme, ThemeSet
from design_system.domain.token.state import StateTokens
from design_system.domain.token.token import (
    DesignToken,
    InvalidTokenError,
    TokenSet,
    TokenValue,
)


# --------------------------------------------------------------------------- #
# Identifiers                                                                   #
# --------------------------------------------------------------------------- #
def test_identifiers_are_typed_and_round_trip():
    tid = TokenId.new()
    assert TokenId.from_string(str(tid)) == tid
    # Different concrete types over the same uuid are not equal.
    assert DSNodeId(tid.value) != TokenId(tid.value)


def test_abstract_identifier_cannot_be_constructed():
    import uuid

    with pytest.raises(InvalidDSIdError):
        Identifier(uuid.uuid4())
    with pytest.raises(InvalidDSIdError):
        DesignSystemSpecId.from_string("not-a-uuid")


# --------------------------------------------------------------------------- #
# Tokens                                                                        #
# --------------------------------------------------------------------------- #
def test_token_value_is_literal_xor_reference():
    with pytest.raises(InvalidTokenError):
        TokenValue(literal="x", ref="y")
    with pytest.raises(InvalidTokenError):
        TokenValue()


def test_primitive_must_be_literal_and_reference_cannot_self_alias():
    with pytest.raises(InvalidTokenError):
        DesignToken(id=TokenId.new(), key="a.b", category=TokenCategory.COLOR,
                    tier=TokenTier.PRIMITIVE, value=TokenValue.alias("c.d"))
    with pytest.raises(InvalidTokenError):
        DesignToken(id=TokenId.new(), key="a.b", category=TokenCategory.COLOR,
                    tier=TokenTier.SEMANTIC, value=TokenValue.alias("a.b"))


def test_token_set_rejects_duplicate_keys():
    a = DesignToken(id=TokenId.new(), key="gray.900", category=TokenCategory.COLOR,
                    tier=TokenTier.PRIMITIVE, value=TokenValue.of("#000"))
    with pytest.raises(InvalidTokenError):
        TokenSet.of([a, a])


# --------------------------------------------------------------------------- #
# Themes                                                                        #
# --------------------------------------------------------------------------- #
def _theme(mode, **overrides):
    return Theme(id=ThemeId.new(), mode=mode, name=mode.value.title(), overrides=overrides)


def test_theme_set_requires_light_and_parity():
    light = _theme(ThemeMode.LIGHT, **{"color.text": "gray.900", "color.bg": "gray.0"})
    dark_ok = _theme(ThemeMode.DARK, **{"color.text": "gray.0", "color.bg": "gray.900"})
    assert ThemeSet.of([light, dark_ok]).has_dark

    dark_bad = _theme(ThemeMode.DARK, **{"color.text": "gray.0"})  # missing color.bg
    with pytest.raises(InvalidThemeError):
        ThemeSet.of([light, dark_bad])
    with pytest.raises(InvalidThemeError):
        ThemeSet.of([dark_ok])  # no light theme


# --------------------------------------------------------------------------- #
# Constraints                                                                   #
# --------------------------------------------------------------------------- #
def _constraint(kind, enforcement=EnforcementLevel.BLOCKING):
    return Constraint(id=ConstraintId.new(), kind=kind, enforcement=enforcement,
                      statement=f"{kind.value} rule")


def test_constraint_set_requires_mandatory_blocking_rules():
    ok = ConstraintSet.of([
        _constraint(ConstraintKind.TOKEN_ONLY),
        _constraint(ConstraintKind.NO_HARDCODED),
    ])
    assert len(ok.blocking()) == 2
    # token_only present but only recommended -> rejected
    with pytest.raises(InvalidConstraintError):
        ConstraintSet.of([
            _constraint(ConstraintKind.TOKEN_ONLY, EnforcementLevel.RECOMMENDED),
            _constraint(ConstraintKind.NO_HARDCODED),
        ])
    # no_hardcoded missing -> rejected
    with pytest.raises(InvalidConstraintError):
        ConstraintSet.of([_constraint(ConstraintKind.TOKEN_ONLY)])


# --------------------------------------------------------------------------- #
# Components                                                                    #
# --------------------------------------------------------------------------- #
def _minimal_component(mappings=None):
    states = ComponentStateSpec(states=(StateTokens(StateKind.DEFAULT, {}),))
    responsive = ResponsiveSpec(behavior={Breakpoint.MOBILE: "stacked"})
    a11y = AccessibilitySpec(role="button", keyboard=("tab",))
    if mappings is None:
        mappings = {
            p: PlatformMapping(platform=p, primitive="c", identifier=f"C-{p.value}")
            for p in (Platform.GENERIC, Platform.SHOPIFY, Platform.MAGENTO)
        }
    return ComponentSpec(
        id=ComponentSpecId.new(), component=ComponentType.FORMS, atomic_level=AtomicLevel.ATOM,
        token_refs=("input.bg",), properties=(), variants=(), states=states,
        responsive=responsive, accessibility=a11y, performance=PerformanceBudget(),
        mappings=mappings,
    )


def test_component_requires_all_three_platform_mappings():
    _minimal_component()  # ok
    with pytest.raises(InvalidComponentSpecError):
        _minimal_component(mappings={
            Platform.GENERIC: PlatformMapping(platform=Platform.GENERIC, primitive="c",
                                              identifier="C"),
            Platform.SHOPIFY: PlatformMapping(platform=Platform.SHOPIFY, primitive="s",
                                              identifier="S"),
        })


def test_component_variant_integrity():
    prop = ComponentProperty(name="variant", type=PropertyType.VARIANT,
                             options=("primary", "secondary"), default="primary")
    states = ComponentStateSpec(states=(StateTokens(StateKind.DEFAULT, {}),))
    responsive = ResponsiveSpec(behavior={Breakpoint.MOBILE: "stacked"})
    a11y = AccessibilitySpec(role="button")
    mappings = {p: PlatformMapping(platform=p, primitive="c", identifier=f"C-{p.value}")
                for p in (Platform.GENERIC, Platform.SHOPIFY, Platform.MAGENTO)}
    # a variant assigning a value outside the property's options is rejected
    bad_variant = ComponentVariant(name="ghost", property_values={"variant": "tertiary"})
    with pytest.raises(InvalidComponentSpecError):
        ComponentSpec(
            id=ComponentSpecId.new(), component=ComponentType.FORMS,
            atomic_level=AtomicLevel.ATOM, token_refs=("input.bg",), properties=(prop,),
            variants=(bad_variant,), states=states, responsive=responsive, accessibility=a11y,
            performance=PerformanceBudget(), mappings=mappings,
        )


# --------------------------------------------------------------------------- #
# Graphs                                                                        #
# --------------------------------------------------------------------------- #
def test_graph_rejects_alias_cycle_and_dangling_edge():
    a, b = DSNodeId.new(), DSNodeId.new()
    nodes = [DSNode(a, NodeKind.TOKEN, "a"), DSNode(b, NodeKind.TOKEN, "b")]
    with pytest.raises(InvalidDSGraphError):
        DSGraph.of(GraphKind.TOKEN, nodes, [
            DSEdge(DSEdgeId.new(), a, b, GraphRelation.ALIASES),
            DSEdge(DSEdgeId.new(), b, a, GraphRelation.ALIASES),
        ])
    with pytest.raises(InvalidDSGraphError):
        DSGraph.of(GraphKind.TOKEN, [DSNode(a, NodeKind.TOKEN, "a")], [
            DSEdge(DSEdgeId.new(), a, b, GraphRelation.ALIASES),  # b not in graph
        ])


# --------------------------------------------------------------------------- #
# Aggregate invariants                                                          #
# --------------------------------------------------------------------------- #
def _built_spec(env_factory, signals):
    import asyncio

    from design_system.application.commands import BuildDesignSystem
    from design_system.application.request import DesignSystemRequest
    from design_system.domain.context.context import DesignSystemBrief, ProjectContext

    env = env_factory(signals)
    req = DesignSystemRequest(
        brief=DesignSystemBrief(product_category="skincare"),
        project=ProjectContext(project_id="p"),
    )
    return asyncio.run(env.engine.build(BuildDesignSystem(request=req)))


def test_aggregate_rejects_ungrounded_token(env_factory, signals):
    spec = _built_spec(env_factory, signals)
    # Add a token citing evidence absent from the graph -> provenance invariant fires.
    rogue = DesignToken(
        id=TokenId.new(), key="rogue.token", category=TokenCategory.COLOR,
        tier=TokenTier.PRIMITIVE, value=TokenValue.of("#123"),
        citations=(Citation(evidence_id=DSEvidenceId.new(), relevance="ungrounded"),),
    )
    bad_tokens = TokenSet.of([*spec.token_set, rogue])
    with pytest.raises(InvalidSpecificationError):
        dataclasses.replace(spec, token_set=bad_tokens)


def test_aggregate_rejects_dangling_component_token(env_factory, signals):
    spec = _built_spec(env_factory, signals)
    some = next(iter(spec.component_specs))
    broken = dataclasses.replace(some, token_refs=(*some.token_refs, "does.not.exist"))
    bad_components = type(spec.component_specs).of(
        [broken if s.component is some.component else s for s in spec.component_specs]
    )
    with pytest.raises(InvalidSpecificationError):
        dataclasses.replace(spec, component_specs=bad_components)


def test_evidence_graph_reports_missing():
    ev = DSEvidence(id=DSEvidenceId.new(), provenance=ProvenanceKind.KNOWLEDGE,
                    external_ref="k", claim="c", confidence=Confidence.of(0.5))
    graph = EvidenceGraph.of([ev])
    assert graph.has(ev.id)
    assert graph.missing([ev.id]) == ()
    absent = DSEvidenceId.new()
    assert graph.missing([absent]) == (absent,)
