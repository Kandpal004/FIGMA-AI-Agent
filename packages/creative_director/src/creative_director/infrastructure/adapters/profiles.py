"""The review profile catalogue — the six calibrated business-model profiles.

Each :class:`ReviewProfile` reweights the fourteen substantive scoring categories, sets the
hard gates that must hold to approve, and defines a default threshold. A Luxury store weights
brand, typography, and trust and gates them high; a Marketplace weights conversion and
performance; an Enterprise gates accessibility, scalability, and maintainability. The *same*
critic outputs are therefore held to different bars by different profiles — the calibration a
25-year Creative Director brings to different clients, encoded as data.

Pure data over the domain profile model. No I/O, no framework.
"""

from __future__ import annotations

from collections.abc import Mapping

from creative_director.domain.policy.profile import ReviewProfile
from creative_director.domain.shared.value_objects import (
    ReviewProfileKind,
    Score,
    ScoreCategory,
    Weight,
)

__all__ = ["profile_for"]

_C = ScoreCategory
_SUBSTANTIVE = (
    _C.BUSINESS, _C.BRAND, _C.UX, _C.ACCESSIBILITY, _C.PERFORMANCE, _C.TRUST,
    _C.TYPOGRAPHY, _C.SPACING, _C.VISUAL_HIERARCHY, _C.CONSISTENCY, _C.SCALABILITY,
    _C.DEVELOPER_EXPERIENCE, _C.MAINTAINABILITY, _C.CONVERSION,
)


def _weights(emphasis: Mapping[ScoreCategory, float]) -> dict[ScoreCategory, Weight]:
    raw = {c: emphasis.get(c, 1.0) for c in _SUBSTANTIVE}
    total = sum(raw.values())
    return {c: Weight(v / total) for c, v in raw.items()}


def _gates(gates: Mapping[ScoreCategory, float]) -> dict[ScoreCategory, Score]:
    return {c: Score(v) for c, v in gates.items()}


_STARTUP = ReviewProfile(
    kind=ReviewProfileKind.STARTUP,
    weights=_weights({_C.CONVERSION: 2.2, _C.UX: 1.8, _C.PERFORMANCE: 1.6, _C.BUSINESS: 1.4,
                      _C.MAINTAINABILITY: 0.6, _C.SCALABILITY: 0.6}),
    hard_gates=_gates({_C.CONVERSION: 55.0, _C.UX: 55.0}),
    default_threshold=Score(65.0),
)

_ENTERPRISE = ReviewProfile(
    kind=ReviewProfileKind.ENTERPRISE,
    weights=_weights({_C.ACCESSIBILITY: 2.0, _C.SCALABILITY: 1.9, _C.MAINTAINABILITY: 1.9,
                      _C.CONSISTENCY: 1.7, _C.DEVELOPER_EXPERIENCE: 1.6, _C.BUSINESS: 1.3}),
    hard_gates=_gates({_C.ACCESSIBILITY: 70.0, _C.SCALABILITY: 65.0, _C.MAINTAINABILITY: 65.0}),
    default_threshold=Score(75.0),
)

_LUXURY = ReviewProfile(
    kind=ReviewProfileKind.LUXURY,
    weights=_weights({_C.BRAND: 2.4, _C.TYPOGRAPHY: 2.2, _C.SPACING: 1.9, _C.VISUAL_HIERARCHY: 1.9,
                      _C.TRUST: 1.8, _C.CONSISTENCY: 1.7, _C.CONVERSION: 0.8}),
    hard_gates=_gates({_C.BRAND: 75.0, _C.TYPOGRAPHY: 75.0, _C.TRUST: 70.0}),
    default_threshold=Score(80.0),
)

_MARKETPLACE = ReviewProfile(
    kind=ReviewProfileKind.MARKETPLACE,
    weights=_weights({_C.CONVERSION: 2.2, _C.PERFORMANCE: 2.0, _C.UX: 1.8, _C.TRUST: 1.6,
                      _C.SCALABILITY: 1.5, _C.TYPOGRAPHY: 0.7}),
    hard_gates=_gates({_C.CONVERSION: 65.0, _C.PERFORMANCE: 65.0}),
    default_threshold=Score(72.0),
)

_D2C = ReviewProfile(
    kind=ReviewProfileKind.D2C,
    weights=_weights({_C.CONVERSION: 2.1, _C.TRUST: 1.9, _C.BRAND: 1.8, _C.UX: 1.6,
                      _C.PERFORMANCE: 1.4}),
    hard_gates=_gates({_C.CONVERSION: 60.0, _C.TRUST: 60.0}),
    default_threshold=Score(70.0),
)

_B2B = ReviewProfile(
    kind=ReviewProfileKind.B2B,
    weights=_weights({_C.DEVELOPER_EXPERIENCE: 2.0, _C.MAINTAINABILITY: 1.9, _C.UX: 1.7,
                      _C.CONSISTENCY: 1.7, _C.SCALABILITY: 1.6, _C.BUSINESS: 1.5,
                      _C.BRAND: 0.7}),
    hard_gates=_gates({_C.DEVELOPER_EXPERIENCE: 65.0, _C.MAINTAINABILITY: 65.0}),
    default_threshold=Score(72.0),
)

_PROFILES: dict[ReviewProfileKind, ReviewProfile] = {
    ReviewProfileKind.STARTUP: _STARTUP,
    ReviewProfileKind.ENTERPRISE: _ENTERPRISE,
    ReviewProfileKind.LUXURY: _LUXURY,
    ReviewProfileKind.MARKETPLACE: _MARKETPLACE,
    ReviewProfileKind.D2C: _D2C,
    ReviewProfileKind.B2B: _B2B,
}


def profile_for(kind: ReviewProfileKind) -> ReviewProfile:
    """Return the calibrated profile for a business model."""
    return _PROFILES[kind]
