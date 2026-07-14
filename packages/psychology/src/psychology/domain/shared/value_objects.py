"""Shared value objects for the Customer Psychology Engine.

These immutable, self-validating value objects are the vocabulary the engine reasons
in: the provenance of the evidence it cites, the awareness and sophistication levels it
classifies, the drivers and needs it models, the behavioral frameworks it applies, the
kinds of matrix and graph it builds, and the calibrated scales it scores everything on.

Everything here is pure domain: only the standard library and the shared-kernel error
base (:mod:`core.errors`). No framework, no I/O, no global mutable state, and no import
of any provider or other engine — those are reached only through ports, keeping this
domain independent.

Testing considerations
----------------------
* :class:`AwarenessLevel` and :class:`SophisticationLevel` each have exactly five
  members; :class:`BehavioralPrincipleKind` has nine (the required principles).
* :class:`Confidence`, :class:`PsychScore`, :class:`Percentage`, :class:`Intensity`,
  :class:`Priority`, and :class:`Likelihood` validate their ranges and order by value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "AnxietyKind",
    "AwarenessLevel",
    "BehavioralPrincipleKind",
    "BuyingRole",
    "Confidence",
    "ConsideredAlternative",
    "CustomerIntent",
    "DriverKind",
    "EmotionKind",
    "FeasibilityBand",
    "FrictionKind",
    "GraphKind",
    "GraphRelation",
    "Intensity",
    "InvalidPsychologyValueError",
    "JobType",
    "JourneyPhase",
    "Likelihood",
    "MaslowNeed",
    "MatrixKind",
    "NodeKind",
    "ObjectionKind",
    "Percentage",
    "Priority",
    "ProvenanceKind",
    "PsychFramework",
    "PsychScore",
    "QualityBand",
    "RiskKind",
    "SophisticationLevel",
    "Tag",
    "TrustRequirementKind",
]


class InvalidPsychologyValueError(DesignDirectorError):
    """Raised when a psychology value object is constructed with invalid data."""

    code = "invalid_psychology_value"
    http_status = 422


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
class ProvenanceKind(str, Enum):
    """Where a piece of cited evidence originates.

    The Brand/Business Strategy engines and the four platform engines today; future
    behavioral data sources (analytics, heatmaps, reviews, …) extend this additively.
    """

    BRAND_STRATEGY = "brand_strategy"
    BUSINESS_STRATEGY = "business_strategy"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    COMPETITOR = "competitor"
    REASONING = "reasoning"
    ANALYTICS = "analytics"
    HEATMAP = "heatmap"
    SESSION_REPLAY = "session_replay"
    CRM = "crm"
    REVIEW = "review"
    SUPPORT = "support"
    SURVEY = "survey"
    NPS = "nps"


# --------------------------------------------------------------------------- #
# Customer state                                                               #
# --------------------------------------------------------------------------- #
class AwarenessLevel(str, Enum):
    """Eugene Schwartz's five stages of customer awareness."""

    UNAWARE = "unaware"
    PROBLEM_AWARE = "problem_aware"
    SOLUTION_AWARE = "solution_aware"
    PRODUCT_AWARE = "product_aware"
    MOST_AWARE = "most_aware"

    @property
    def rank(self) -> int:
        order = [
            AwarenessLevel.UNAWARE,
            AwarenessLevel.PROBLEM_AWARE,
            AwarenessLevel.SOLUTION_AWARE,
            AwarenessLevel.PRODUCT_AWARE,
            AwarenessLevel.MOST_AWARE,
        ]
        return order.index(self)


class SophisticationLevel(str, Enum):
    """Eugene Schwartz's five stages of market sophistication."""

    STAGE_1_NEW = "stage_1_new"  # first to market — the plain claim works
    STAGE_2_AMPLIFIED_CLAIM = "stage_2_amplified_claim"  # bigger claims
    STAGE_3_MECHANISM = "stage_3_mechanism"  # a new mechanism/how
    STAGE_4_AMPLIFIED_MECHANISM = "stage_4_amplified_mechanism"  # a better mechanism
    STAGE_5_IDENTIFICATION = "stage_5_identification"  # identity/experience over claim

    @property
    def rank(self) -> int:
        order = [
            SophisticationLevel.STAGE_1_NEW,
            SophisticationLevel.STAGE_2_AMPLIFIED_CLAIM,
            SophisticationLevel.STAGE_3_MECHANISM,
            SophisticationLevel.STAGE_4_AMPLIFIED_MECHANISM,
            SophisticationLevel.STAGE_5_IDENTIFICATION,
        ]
        return order.index(self)


class CustomerIntent(str, Enum):
    """The customer's purchase intent state."""

    RESEARCHING = "researching"
    COMPARING = "comparing"
    READY = "ready"
    HESITATING = "hesitating"
    RETURNING = "returning"


class BuyingRole(str, Enum):
    """A role a person plays in the buying decision."""

    ECONOMIC_BUYER = "economic_buyer"
    USER = "user"
    CHAMPION = "champion"
    BLOCKER = "blocker"
    DECIDER = "decider"


class JobType(str, Enum):
    """The category of a job-to-be-done (Christensen)."""

    FUNCTIONAL = "functional"
    EMOTIONAL = "emotional"
    SOCIAL = "social"


class JourneyPhase(str, Enum):
    """A phase in the customer buying journey."""

    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    DECISION = "decision"
    PURCHASE = "purchase"
    POST_PURCHASE = "post_purchase"
    ADVOCACY = "advocacy"


# --------------------------------------------------------------------------- #
# Drivers, emotions, friction                                                  #
# --------------------------------------------------------------------------- #
class DriverKind(str, Enum):
    """The kind of psychological driver moving the decision."""

    EMOTIONAL = "emotional"
    LOGICAL = "logical"
    SOCIAL = "social"
    URGENCY = "urgency"
    RETENTION = "retention"


class EmotionKind(str, Enum):
    """An emotion in play during the buying decision."""

    TRUST = "trust"
    DESIRE = "desire"
    CONFIDENCE = "confidence"
    ANXIETY = "anxiety"
    FEAR = "fear"
    EXCITEMENT = "excitement"
    RELIEF = "relief"
    BELONGING = "belonging"
    ASPIRATION = "aspiration"
    REGRET = "regret"
    REASSURANCE = "reassurance"


class AnxietyKind(str, Enum):
    """A kind of purchase anxiety."""

    FINANCIAL = "financial"
    PERFORMANCE = "performance"
    SOCIAL = "social"
    TIME = "time"
    TRUST = "trust"
    COMPLEXITY = "complexity"
    COMMITMENT = "commitment"


class FrictionKind(str, Enum):
    """A kind of purchase friction."""

    COGNITIVE = "cognitive"
    INFORMATIONAL = "informational"
    PROCESS = "process"
    PRICE = "price"
    TRUST = "trust"
    DECISION_FATIGUE = "decision_fatigue"


class RiskKind(str, Enum):
    """A kind of perceived purchase risk."""

    FINANCIAL = "financial"
    FUNCTIONAL = "functional"
    PHYSICAL = "physical"
    SOCIAL = "social"
    PSYCHOLOGICAL = "psychological"
    TIME = "time"


class TrustRequirementKind(str, Enum):
    """A kind of trust the customer requires before committing."""

    SOCIAL_PROOF = "social_proof"
    AUTHORITY = "authority"
    GUARANTEE = "guarantee"
    TRANSPARENCY = "transparency"
    SECURITY = "security"
    CONSISTENCY = "consistency"
    EXPERTISE = "expertise"


class ObjectionKind(str, Enum):
    """A kind of purchase objection."""

    PRICE = "price"
    NEED = "need"
    TRUST = "trust"
    URGENCY = "urgency"
    FIT = "fit"
    RISK = "risk"
    COMPARISON = "comparison"


# --------------------------------------------------------------------------- #
# Frameworks                                                                   #
# --------------------------------------------------------------------------- #
class PsychFramework(str, Enum):
    """A behavioral-science framework the engine applies."""

    MASLOW = "maslow"
    FOGG = "fogg"
    HOOK = "hook"
    JTBD = "jtbd"
    BEHAVIORAL_ECONOMICS = "behavioral_economics"


class MaslowNeed(str, Enum):
    """A level in Maslow's hierarchy of needs."""

    PHYSIOLOGICAL = "physiological"
    SAFETY = "safety"
    BELONGING = "belonging"
    ESTEEM = "esteem"
    SELF_ACTUALIZATION = "self_actualization"


class BehavioralPrincipleKind(str, Enum):
    """A behavioral-economics / persuasion principle (Cialdini + BE)."""

    LOSS_AVERSION = "loss_aversion"
    ANCHORING = "anchoring"
    SCARCITY = "scarcity"
    SOCIAL_PROOF = "social_proof"
    AUTHORITY = "authority"
    COMMITMENT = "commitment"
    RECIPROCITY = "reciprocity"
    CHOICE_ARCHITECTURE = "choice_architecture"
    PEAK_END = "peak_end"


class FeasibilityBand(str, Enum):
    """The Fogg behavior-feasibility band (from motivation × ability × prompt)."""

    LIKELY = "likely"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"


# --------------------------------------------------------------------------- #
# Matrices & graphs                                                            #
# --------------------------------------------------------------------------- #
class MatrixKind(str, Enum):
    """One of the psychology matrices."""

    OBJECTION = "objection"
    TRUST = "trust"
    MOTIVATION = "motivation"
    EMOTION = "emotion"
    BEHAVIOR = "behavior"
    RISK = "risk"
    VALUE = "value"
    CONFIDENCE = "confidence"
    RETENTION = "retention"


class GraphKind(str, Enum):
    """One of the six psychology graphs."""

    DECISION = "decision"
    EMOTION = "emotion"
    TRUST = "trust"
    OBJECTION = "objection"
    MOTIVATION = "motivation"
    BEHAVIOR = "behavior"


class NodeKind(str, Enum):
    """The kind of node a psychology-graph node represents."""

    DECISION_FACTOR = "decision_factor"
    TRIGGER = "trigger"
    BLOCKER = "blocker"
    EMOTION = "emotion"
    TRUST = "trust"
    OBJECTION = "objection"
    RESOLUTION = "resolution"
    MOTIVATION = "motivation"
    NEED = "need"
    BEHAVIOR = "behavior"
    DRIVER = "driver"


class GraphRelation(str, Enum):
    """A typed, directed edge between two psychology-graph nodes.

    ``LEADS_TO`` and ``DERIVES_FROM`` must be acyclic. ``CONFLICTS_WITH`` may be mutual —
    a tension to resolve, not an error.
    """

    LEADS_TO = "leads_to"
    BLOCKS = "blocks"
    RESOLVES = "resolves"
    REINFORCES = "reinforces"
    TRIGGERS = "triggers"
    DERIVES_FROM = "derives_from"
    CONFLICTS_WITH = "conflicts_with"


class QualityBand(str, Enum):
    """A categorical band shared by the quality/score scales."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


# --------------------------------------------------------------------------- #
# Calibrated scales                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """A confidence value in ``[0, 1]``."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidPsychologyValueError(
                "Confidence.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(1.0, max(0.0, value)))


@dataclass(frozen=True, slots=True, order=True)
class Percentage:
    """A fraction in ``[0, 1]`` (e.g. a coverage or grounding ratio)."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidPsychologyValueError(
                "Percentage.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def ratio(cls, present: int, total: int) -> Self:
        """The fraction ``present / total`` (1.0 when nothing is expected)."""
        if total <= 0:
            return cls(value=1.0)
        return cls(value=min(1.0, max(0.0, present / total)))


@dataclass(frozen=True, slots=True, order=True)
class PsychScore:
    """A score in ``[0, 100]`` with a calibrated band."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise InvalidPsychologyValueError(
                "PsychScore.value must be within [0, 100].", details={"value": self.value}
            )

    @property
    def band(self) -> QualityBand:
        if self.value >= 80.0:
            return QualityBand.EXCELLENT
        if self.value >= 60.0:
            return QualityBand.GOOD
        if self.value >= 40.0:
            return QualityBand.FAIR
        return QualityBand.POOR

    @classmethod
    def of(cls, value: float) -> Self:
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        return cls(value=min(100.0, max(0.0, value)))


def _bounded_int(name: str, value: int, low: int, high: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidPsychologyValueError(f"{name} must be an int.", details={"value": value})
    if not low <= value <= high:
        raise InvalidPsychologyValueError(
            f"{name} must be within [{low}, {high}].", details={"value": value}
        )
    return value


@dataclass(frozen=True, slots=True, order=True)
class Intensity:
    """A 1–5 intensity/strength (5 = strongest)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Intensity", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Priority:
    """A 1–5 priority (5 = highest)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Priority", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class Likelihood:
    """A 1–5 likelihood (5 = most likely)."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _bounded_int("Likelihood", self.value, 1, 5))

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class ConsideredAlternative:
    """A runner-up interpretation the engine weighed and rejected — the trade-off record.

    A behavioral scientist does not just state a determination; they show what else fit
    the evidence and why it lost. Recording the considered alternative keeps every
    determination honest and auditable.

    Attributes:
        option: The alternative that was considered.
        reason_rejected: Why it was not chosen.
    """

    option: str
    reason_rejected: str

    def __post_init__(self) -> None:
        if not self.option or not self.option.strip():
            raise InvalidPsychologyValueError("ConsideredAlternative.option must be non-empty.")
        if not self.reason_rejected or not self.reason_rejected.strip():
            raise InvalidPsychologyValueError(
                "ConsideredAlternative.reason_rejected must be non-empty."
            )


_TAG_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Tag:
    """A normalized free-form label (lower case, whitespace collapsed to hyphens)."""

    value: str

    def __post_init__(self) -> None:
        normalized = _TAG_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidPsychologyValueError("Tag must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        return cls(value=value)
