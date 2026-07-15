"""The component specification — the complete, cited contract for one component.

A :class:`ComponentSpec` is everything the design system says about one of the forty-one
components: its atomic level, the tokens it consumes, its configurable properties and named
variants, its supported states and responsive behaviour, its accessibility and performance
budget, and — mandatorily — its developer, Shopify, and Magento platform mappings. Nothing about
a component is left implicit, and every spec is grounded in cited evidence.

Two structural invariants hold at construction:

* **Platform completeness** — a spec must carry a mapping for the generic developer contract
  *and* for Shopify *and* for Magento. A component that cannot be realised on every target
  platform is rejected, not silently degraded.
* **Variant integrity** — every variant only assigns properties the component declares, and only
  values those properties allow.

A :class:`ComponentSpecSet` is the immutable, unique-by-type registry of every component spec.

Pure domain: standard library, the shared-kernel error base, DS ids, evidence, the variant and
mapping models, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.component.mapping import PlatformMapping
from design_system.domain.component.variant import (
    ComponentProperty,
    ComponentStateSpec,
    ComponentVariant,
    ResponsiveSpec,
)
from design_system.domain.evidence.evidence import Citation
from design_system.domain.shared.ids import ComponentSpecId
from design_system.domain.shared.value_objects import (
    AtomicLevel,
    ComponentType,
    Platform,
    PropertyType,
    Tag,
)

__all__ = [
    "AccessibilitySpec",
    "ComponentSpec",
    "ComponentSpecSet",
    "InvalidComponentSpecError",
    "PerformanceBudget",
]

# The platforms every component spec must map to.
_REQUIRED_PLATFORMS = (Platform.GENERIC, Platform.SHOPIFY, Platform.MAGENTO)


class InvalidComponentSpecError(DesignDirectorError):
    """Raised when a component specification violates a structural invariant."""

    code = "invalid_design_system_component_spec"
    http_status = 422


@dataclass(frozen=True, slots=True)
class AccessibilitySpec:
    """The accessibility contract a component must satisfy.

    Attributes:
        role: The ARIA role (or native element) the component maps to.
        keyboard: The keyboard-interaction requirements (e.g. ``("tab", "enter", "escape")``).
        min_contrast: The minimum text contrast ratio required (e.g. ``4.5`` for AA body text).
        focus_visible: Whether a visible focus indicator is mandatory.
        notes: Additional a11y guidance (labels, live regions, reduced motion, …).
    """

    role: str
    keyboard: tuple[str, ...] = ()
    min_contrast: float = 4.5
    focus_visible: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.role or not self.role.strip():
            raise InvalidComponentSpecError("AccessibilitySpec.role must be non-empty.")
        if not self.min_contrast > 0:
            raise InvalidComponentSpecError("AccessibilitySpec.min_contrast must be positive.")
        object.__setattr__(self, "role", self.role.strip())
        object.__setattr__(
            self,
            "keyboard",
            tuple(dict.fromkeys(k.strip().lower() for k in self.keyboard if k and k.strip())),
        )


@dataclass(frozen=True, slots=True)
class PerformanceBudget:
    """The performance envelope a component must fit within.

    Attributes:
        lazy_load: Whether the component should defer below-the-fold work.
        max_dom_nodes: A soft ceiling on rendered DOM nodes (0 = unspecified).
        blocks_lcp: Whether the component can appear in the largest-contentful-paint element.
        notes: Additional performance guidance (image budgets, hydration strategy, …).
    """

    lazy_load: bool = False
    max_dom_nodes: int = 0
    blocks_lcp: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if self.max_dom_nodes < 0:
            raise InvalidComponentSpecError("PerformanceBudget.max_dom_nodes must be >= 0.")


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    """The complete, cited specification for one component.

    Attributes:
        id: Spec identity within this specification.
        component: Which of the forty-one components this specifies.
        atomic_level: The atomic-design level.
        token_refs: The semantic/component token keys this component consumes.
        properties: The configurable properties.
        variants: The named variant combinations.
        states: The states the component supports and the tokens each activates.
        responsive: How the component adapts across breakpoints.
        accessibility: The accessibility contract.
        performance: The performance budget.
        mappings: The platform mappings — must cover GENERIC, SHOPIFY and MAGENTO.
        citations: The evidence supporting this component (must resolve in the evidence graph).
        tags: Free-form tags for filtering.
    """

    id: ComponentSpecId
    component: ComponentType
    atomic_level: AtomicLevel
    token_refs: tuple[str, ...]
    properties: tuple[ComponentProperty, ...]
    variants: tuple[ComponentVariant, ...]
    states: ComponentStateSpec
    responsive: ResponsiveSpec
    accessibility: AccessibilitySpec
    performance: PerformanceBudget
    mappings: Mapping[Platform, PlatformMapping]
    citations: tuple[Citation, ...] = ()
    tags: frozenset[Tag] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        token_refs = tuple(
            dict.fromkeys(t.strip().lower() for t in self.token_refs if t and t.strip())
        )
        if not token_refs:
            raise InvalidComponentSpecError(
                "A ComponentSpec must consume at least one token (no hard-coded values).",
                details={"component": self.component.value},
            )
        props = {p.name: p for p in self.properties}
        if len(props) != len(self.properties):
            raise InvalidComponentSpecError(
                "Component properties must be unique by name.",
                details={"component": self.component.value},
            )
        self._validate_variants(props)
        self._validate_mappings()
        object.__setattr__(self, "token_refs", token_refs)
        object.__setattr__(self, "properties", tuple(self.properties))
        object.__setattr__(self, "variants", tuple(self.variants))
        object.__setattr__(self, "citations", tuple(self.citations))
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "mappings", MappingProxyType(dict(self.mappings)))

    def _validate_variants(self, props: dict[str, ComponentProperty]) -> None:
        for variant in self.variants:
            for name, value in variant.property_values.items():
                prop = props.get(name)
                if prop is None:
                    raise InvalidComponentSpecError(
                        f"Variant {variant.name!r} assigns unknown property {name!r}.",
                        details={"component": self.component.value},
                    )
                if prop.type is PropertyType.VARIANT and value not in prop.options:
                    raise InvalidComponentSpecError(
                        f"Variant {variant.name!r} assigns {name}={value!r}, "
                        "not among the property's options.",
                        details={"component": self.component.value, "options": list(prop.options)},
                    )

    def _validate_mappings(self) -> None:
        for platform, mapping in self.mappings.items():
            if mapping.platform is not platform:
                raise InvalidComponentSpecError(
                    "Mapping key must match its platform.",
                    details={"key": platform.value, "mapping": mapping.platform.value},
                )
        missing = [p for p in _REQUIRED_PLATFORMS if p not in self.mappings]
        if missing:
            raise InvalidComponentSpecError(
                "A ComponentSpec must map to the developer contract, Shopify and Magento.",
                details={
                    "component": self.component.value,
                    "missing": [p.value for p in missing],
                },
            )

    @property
    def evidence_ids(self) -> tuple:
        return tuple(c.evidence_id for c in self.citations)

    def mapping_for(self, platform: Platform) -> PlatformMapping:
        mapping = self.mappings.get(platform)
        if mapping is None:
            raise InvalidComponentSpecError(
                f"No mapping for platform {platform.value}.",
                details={"component": self.component.value},
            )
        return mapping


@dataclass(frozen=True, slots=True)
class ComponentSpecSet:
    """The immutable, unique-by-component registry of every component spec."""

    items: Mapping[ComponentType, ComponentSpec] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def of(cls, specs: Iterable[ComponentSpec]) -> ComponentSpecSet:
        """Build a set keyed by component type.

        Raises:
            InvalidComponentSpecError: If two specs target the same component.
        """
        mapping: dict[ComponentType, ComponentSpec] = {}
        for spec in specs:
            if spec.component in mapping:
                raise InvalidComponentSpecError(
                    "Duplicate component spec.", details={"component": spec.component.value}
                )
            mapping[spec.component] = spec
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def __contains__(self, component: ComponentType) -> bool:
        return component in self.items

    def get(self, component: ComponentType) -> ComponentSpec:
        spec = self.items.get(component)
        if spec is None:
            raise InvalidComponentSpecError(
                f"No spec for component {component.value}.",
                details={"component": component.value},
            )
        return spec

    def components(self) -> tuple[ComponentType, ...]:
        return tuple(self.items.keys())
