"""Shared value objects for the Director domain.

A *value object* has no identity: it is defined entirely by its attributes, is
immutable, and two instances with equal attributes are interchangeable. This
module collects the value objects that describe *how* the Director runs a
workflow — what kind of page is being designed, how retries and rollbacks
behave, how approvals are obtained, and in what execution mode a run proceeds.

Everything here is pure domain: it depends only on the standard library and the
shared-kernel error base (:mod:`core.errors`). There are no framework,
infrastructure, LLM, or MCP imports, and nothing here performs I/O, reads a
clock, or touches global state — every policy is a deterministic, self-validating
value that can be constructed and tested in isolation.

Contents
--------
* :class:`PageType`       — the storefront page kinds the platform designs.
* :class:`WorkflowType`   — page-level vs section-level workflow (the two-tier model).
* :class:`ExecutionMode`  — synchronous, asynchronous, or dry-run execution.
* :class:`Priority`       — scheduling priority (ordered).
* :class:`BackoffStrategy`— how retry delays grow.
* :class:`RetryPolicy`    — bounded retry behaviour with deterministic backoff.
* :class:`Attempt`        — an immutable, monotonically-advancing attempt counter.
* :class:`RollbackStrategy` / :class:`RollbackPolicy` — how a rejection rewinds a run.
* :class:`ApprovalMode`   / :class:`ApprovalPolicy`   — how a gate is approved.

Testing considerations
----------------------
* Every dataclass is frozen: attribute assignment raises ``FrozenInstanceError``.
* Every validator rejects out-of-range input with :class:`InvalidPolicyError`
  (e.g. ``max_attempts=0``, ``max_delay < base_delay``, ``multiplier < 1``,
  a manual :class:`ApprovalPolicy` with ``required_approvals=0``).
* :meth:`RetryPolicy.delay_seconds` is deterministic and monotonic per strategy,
  returns ``0`` for the initial attempt, and never exceeds ``max_delay_seconds``.
* :meth:`Attempt.increment` advances by one and raises
  :class:`AttemptsExhaustedError` once the limit is reached; instances are equal
  iff ``(number, limit)`` match.
* :class:`Priority` compares by rank (``URGENT > NORMAL > LOW``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "ApprovalMode",
    "ApprovalPolicy",
    "Attempt",
    "AttemptsExhaustedError",
    "BackoffStrategy",
    "ExecutionMode",
    "InvalidPolicyError",
    "PageType",
    "Priority",
    "RetryPolicy",
    "RollbackPolicy",
    "RollbackStrategy",
    "WorkflowType",
]


# --------------------------------------------------------------------------- #
# Domain exceptions
# --------------------------------------------------------------------------- #
class InvalidPolicyError(DesignDirectorError):
    """Raised when a policy value object is constructed with invalid attributes.

    Extends the shared-kernel :class:`~core.errors.DesignDirectorError` so the
    API layer can translate it uniformly (HTTP 422) while remaining specific
    enough for the domain and tests to branch on.
    """

    code = "invalid_policy"
    http_status = 422


class AttemptsExhaustedError(DesignDirectorError):
    """Raised when an :class:`Attempt` is advanced past its permitted limit."""

    code = "attempts_exhausted"
    http_status = 409


# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #
class PageType(str, Enum):
    """The kinds of storefront page the platform can design.

    The value is the stable identifier used in persistence, the workflow
    catalog, and logs. :data:`CUSTOM` is the escape hatch for pages that do not
    fit a first-class template.
    """

    HOMEPAGE = "homepage"
    COLLECTION = "collection"
    PRODUCT = "product"
    CART = "cart"
    CHECKOUT = "checkout"
    LANDING = "landing"
    BLOG = "blog"
    CUSTOM = "custom"


class WorkflowType(str, Enum):
    """The two tiers of the approved workflow model.

    * :data:`PAGE`    — a page-level workflow that decides *which* sections a
      page comprises and in what order; each of its steps drives a section run.
    * :data:`SECTION` — a section-level workflow: the inner design pipeline
      (research → … → creative-director gate) executed for a single section.
    """

    PAGE = "page"
    SECTION = "section"


class ExecutionMode(str, Enum):
    """How a run is executed.

    * :data:`SYNCHRONOUS`  — driven inline by the caller (tests, small runs).
    * :data:`ASYNCHRONOUS` — enqueued and driven by a background worker; the
      normal production mode for long, resumable runs.
    * :data:`DRY_RUN`      — plan and traverse states without invoking agents;
      used for previewing a plan or validating a workflow definition.
    """

    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    DRY_RUN = "dry_run"


class Priority(IntEnum):
    """Scheduling priority for a run or step.

    An :class:`enum.IntEnum` so priorities compare by rank
    (``Priority.URGENT > Priority.NORMAL``), which lets a scheduler order work
    without a separate mapping. The numeric gaps leave room for future levels.
    """

    LOW = 10
    NORMAL = 20
    HIGH = 30
    URGENT = 40

    @classmethod
    def default(cls) -> Priority:
        """The default priority applied when none is specified."""
        return cls.NORMAL


class BackoffStrategy(str, Enum):
    """How the delay between successive retries grows.

    * :data:`FIXED`       — constant delay every retry.
    * :data:`LINEAR`      — delay grows by ``base_delay`` each retry.
    * :data:`EXPONENTIAL` — delay grows by ``multiplier`` each retry.
    """

    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


class RollbackStrategy(str, Enum):
    """What a run does when a step is rejected.

    Kept intentionally target-agnostic — the concrete step a run rewinds to is
    resolved by the Workflow Engine against a specific workflow definition, not
    encoded here. This keeps the value object reusable across workflows.

    * :data:`NONE`        — do not rewind; the run stops for human handling.
    * :data:`PREVIOUS`    — rewind one step.
    * :data:`STEPS_BACK`  — rewind ``steps_back`` steps.
    * :data:`TO_TARGET`   — rewind to a named target step (``target``).
    * :data:`RESTART`     — rewind to the first step of the workflow.
    """

    NONE = "none"
    PREVIOUS = "previous"
    STEPS_BACK = "steps_back"
    TO_TARGET = "to_target"
    RESTART = "restart"


class ApprovalMode(str, Enum):
    """How approval is obtained at a gate step.

    * :data:`AUTOMATIC` — the system/agent decides; no human sign-off required.
    * :data:`MANUAL`    — one or more human approvals are required to advance.
    """

    AUTOMATIC = "automatic"
    MANUAL = "manual"


# --------------------------------------------------------------------------- #
# Policy value objects
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """A bounded retry policy with deterministic backoff.

    Describes *how many* times a step may run and *how long* to wait before each
    retry. Delay computation is pure and deterministic — no randomness, no jitter,
    no clock — so it is fully unit-testable. (Jitter, which requires an injected
    source of randomness, is deliberately out of scope for this value object.)

    Attributes:
        max_attempts: Total permitted attempts including the first (``>= 1``).
            ``1`` means "no retries".
        backoff: The :class:`BackoffStrategy` governing delay growth.
        base_delay_seconds: Base delay in seconds (``>= 0``).
        max_delay_seconds: Upper bound on any computed delay
            (``>= base_delay_seconds``).
        multiplier: Growth factor for :data:`BackoffStrategy.EXPONENTIAL`
            (``>= 1.0``); ignored by other strategies.
    """

    max_attempts: int = 1
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise InvalidPolicyError(
                "RetryPolicy.max_attempts must be >= 1.",
                details={"max_attempts": self.max_attempts},
            )
        if self.base_delay_seconds < 0:
            raise InvalidPolicyError(
                "RetryPolicy.base_delay_seconds must be >= 0.",
                details={"base_delay_seconds": self.base_delay_seconds},
            )
        if self.max_delay_seconds < self.base_delay_seconds:
            raise InvalidPolicyError(
                "RetryPolicy.max_delay_seconds must be >= base_delay_seconds.",
                details={
                    "base_delay_seconds": self.base_delay_seconds,
                    "max_delay_seconds": self.max_delay_seconds,
                },
            )
        if self.multiplier < 1.0:
            raise InvalidPolicyError(
                "RetryPolicy.multiplier must be >= 1.0.",
                details={"multiplier": self.multiplier},
            )

    @classmethod
    def none(cls) -> Self:
        """A policy that permits a single attempt and no retries."""
        return cls(max_attempts=1)

    @classmethod
    def default(cls) -> Self:
        """A sensible general-purpose policy: 3 attempts, exponential backoff."""
        return cls(
            max_attempts=3,
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay_seconds=1.0,
            max_delay_seconds=30.0,
            multiplier=2.0,
        )

    def allows_retry(self, attempts_made: int) -> bool:
        """Whether another attempt is permitted after ``attempts_made`` attempts.

        Args:
            attempts_made: The number of attempts already performed (``>= 0``).

        Returns:
            ``True`` if a further attempt is within ``max_attempts``.
        """
        return attempts_made < self.max_attempts

    def delay_seconds(self, attempt_number: int) -> float:
        """The delay to wait *before* making attempt ``attempt_number``.

        The initial attempt (``attempt_number <= 1``) has zero delay. Retries
        (``attempt_number >= 2``) grow according to :attr:`backoff` and are
        clamped to :attr:`max_delay_seconds`.

        Args:
            attempt_number: The 1-based attempt about to be made.

        Returns:
            A non-negative delay in seconds, never exceeding
            :attr:`max_delay_seconds`.
        """
        if attempt_number <= 1:
            return 0.0

        retry_index = attempt_number - 1  # 1 for the first retry, 2 for the next…
        if self.backoff is BackoffStrategy.FIXED:
            raw = self.base_delay_seconds
        elif self.backoff is BackoffStrategy.LINEAR:
            raw = self.base_delay_seconds * retry_index
        else:  # EXPONENTIAL
            raw = self.base_delay_seconds * (self.multiplier ** (retry_index - 1))

        return float(min(raw, self.max_delay_seconds))


@dataclass(frozen=True, slots=True)
class Attempt:
    """An immutable attempt counter bounded by a limit.

    Represents "attempt N of at most ``limit``". Because it is immutable,
    advancing produces a *new* :class:`Attempt` via :meth:`increment` rather than
    mutating in place — which keeps a run's history a clean sequence of values.

    Attributes:
        number: The current 1-based attempt number (``1 <= number <= limit``).
        limit: The maximum permitted attempts (``>= 1``); equals a
            :class:`RetryPolicy`'s ``max_attempts``.
    """

    number: int
    limit: int

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise InvalidPolicyError(
                "Attempt.limit must be >= 1.", details={"limit": self.limit}
            )
        if self.number < 1:
            raise InvalidPolicyError(
                "Attempt.number must be >= 1.", details={"number": self.number}
            )
        if self.number > self.limit:
            raise InvalidPolicyError(
                "Attempt.number must not exceed limit.",
                details={"number": self.number, "limit": self.limit},
            )

    @classmethod
    def first(cls, limit: int) -> Self:
        """The first attempt for a given limit."""
        return cls(number=1, limit=limit)

    @classmethod
    def from_policy(cls, policy: RetryPolicy) -> Self:
        """The first attempt sized to a :class:`RetryPolicy`'s ``max_attempts``."""
        return cls(number=1, limit=policy.max_attempts)

    @property
    def is_first(self) -> bool:
        """Whether this is the initial attempt."""
        return self.number == 1

    @property
    def is_exhausted(self) -> bool:
        """Whether the limit has been reached and no further retry is possible."""
        return self.number >= self.limit

    @property
    def remaining(self) -> int:
        """The number of further attempts permitted after this one."""
        return self.limit - self.number

    def increment(self) -> Self:
        """Return the next attempt.

        Returns:
            A new :class:`Attempt` with ``number + 1``.

        Raises:
            AttemptsExhaustedError: If the limit has already been reached.
        """
        if self.is_exhausted:
            raise AttemptsExhaustedError(
                "No attempts remaining.",
                details={"number": self.number, "limit": self.limit},
            )
        return type(self)(number=self.number + 1, limit=self.limit)


@dataclass(frozen=True, slots=True)
class RollbackPolicy:
    """How a run rewinds when a step is rejected.

    Holds *intent*; the Workflow Engine resolves that intent against a concrete
    workflow definition to select the actual step to rewind to. This separation
    keeps the policy reusable and free of any specific workflow's step names.

    Attributes:
        strategy: The :class:`RollbackStrategy` to apply.
        steps_back: Number of steps to rewind — required (``>= 1``) for
            :data:`RollbackStrategy.STEPS_BACK`, otherwise must be ``0``.
        target: The name of the step to rewind to — required (non-empty) for
            :data:`RollbackStrategy.TO_TARGET`, otherwise must be ``None``.
    """

    strategy: RollbackStrategy = RollbackStrategy.NONE
    steps_back: int = 0
    target: str | None = None

    def __post_init__(self) -> None:
        if self.steps_back < 0:
            raise InvalidPolicyError(
                "RollbackPolicy.steps_back must be >= 0.",
                details={"steps_back": self.steps_back},
            )
        if self.strategy is RollbackStrategy.STEPS_BACK:
            if self.steps_back < 1:
                raise InvalidPolicyError(
                    "RollbackStrategy.STEPS_BACK requires steps_back >= 1.",
                    details={"steps_back": self.steps_back},
                )
        elif self.steps_back != 0:
            raise InvalidPolicyError(
                "steps_back is only valid with RollbackStrategy.STEPS_BACK.",
                details={"strategy": self.strategy.value, "steps_back": self.steps_back},
            )

        if self.strategy is RollbackStrategy.TO_TARGET:
            if not self.target:
                raise InvalidPolicyError(
                    "RollbackStrategy.TO_TARGET requires a non-empty target.",
                    details={"strategy": self.strategy.value},
                )
        elif self.target is not None:
            raise InvalidPolicyError(
                "target is only valid with RollbackStrategy.TO_TARGET.",
                details={"strategy": self.strategy.value, "target": self.target},
            )

    @classmethod
    def none(cls) -> Self:
        """No rollback — the run halts for human handling on rejection."""
        return cls(strategy=RollbackStrategy.NONE)

    @classmethod
    def previous(cls) -> Self:
        """Rewind exactly one step on rejection."""
        return cls(strategy=RollbackStrategy.PREVIOUS)

    @classmethod
    def to_target(cls, target: str) -> Self:
        """Rewind to a named target step on rejection."""
        return cls(strategy=RollbackStrategy.TO_TARGET, target=target)

    @classmethod
    def steps(cls, steps_back: int) -> Self:
        """Rewind a fixed number of steps on rejection."""
        return cls(strategy=RollbackStrategy.STEPS_BACK, steps_back=steps_back)

    @property
    def rewinds(self) -> bool:
        """Whether this policy causes any rewind at all."""
        return self.strategy is not RollbackStrategy.NONE


@dataclass(frozen=True, slots=True)
class ApprovalPolicy:
    """How a gate step obtains approval before a run may advance past it.

    Attributes:
        mode: :data:`ApprovalMode.AUTOMATIC` (system/agent decides) or
            :data:`ApprovalMode.MANUAL` (human sign-off required).
        required_approvals: Number of distinct approvals needed. Must be ``0``
            for :data:`ApprovalMode.AUTOMATIC` and ``>= 1`` for
            :data:`ApprovalMode.MANUAL` (supporting multi-approver gates).
    """

    mode: ApprovalMode = ApprovalMode.AUTOMATIC
    required_approvals: int = 0

    def __post_init__(self) -> None:
        if self.mode is ApprovalMode.AUTOMATIC and self.required_approvals != 0:
            raise InvalidPolicyError(
                "AUTOMATIC approval requires required_approvals == 0.",
                details={"required_approvals": self.required_approvals},
            )
        if self.mode is ApprovalMode.MANUAL and self.required_approvals < 1:
            raise InvalidPolicyError(
                "MANUAL approval requires required_approvals >= 1.",
                details={"required_approvals": self.required_approvals},
            )

    @classmethod
    def automatic(cls) -> Self:
        """No human approval required; the system/agent decides."""
        return cls(mode=ApprovalMode.AUTOMATIC, required_approvals=0)

    @classmethod
    def manual(cls, required_approvals: int = 1) -> Self:
        """Require ``required_approvals`` human sign-offs to advance."""
        return cls(mode=ApprovalMode.MANUAL, required_approvals=required_approvals)

    @property
    def requires_human(self) -> bool:
        """Whether advancing past the gate needs at least one human approval."""
        return self.mode is ApprovalMode.MANUAL
