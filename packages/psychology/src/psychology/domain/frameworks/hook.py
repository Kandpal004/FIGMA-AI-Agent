"""The Hook Model — Trigger → Action → Variable Reward → Investment.

A :class:`HookLoop` models how the offer builds a habit (Eyal): the trigger that starts
the loop, the action it prompts, the variable reward that satisfies, and the investment
that loads the next trigger. Used ethically, this is how retention compounds; the loop
carries a guardrail so it never becomes manipulative.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId

__all__ = ["HookLoop", "InvalidHookError"]


class InvalidHookError(DesignDirectorError):
    """Raised when a hook loop is constructed with invalid data."""

    code = "invalid_hook_loop"
    http_status = 422


@dataclass(frozen=True, slots=True)
class HookLoop:
    """The cited habit-forming loop for the offer.

    Attributes:
        trigger: What starts the loop (external or internal).
        action: The simplest action it prompts.
        variable_reward: The reward that satisfies the action.
        investment: The investment that loads the next trigger.
        ethical_guardrail: The rule that keeps the loop honest, not manipulative.
        evidence_ids: The evidence supporting it.
    """

    trigger: str
    action: str
    variable_reward: str
    investment: str
    ethical_guardrail: str = (
        "The loop must serve a real customer goal; no compulsion or deceptive rewards."
    )
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("trigger", "action", "variable_reward", "investment"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise InvalidHookError(f"HookLoop.{name} must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
