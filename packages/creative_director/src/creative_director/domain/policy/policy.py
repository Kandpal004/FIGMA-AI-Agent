"""The ReviewPolicy — the rules a specific review runs under.

A :class:`ReviewPolicy` binds a :class:`ReviewProfile` to a run: the review mode (automatic,
human-assisted, override, or committee) and an optional threshold override (so a caller can
raise or lower the bar for one review without redefining the profile). It is the single
object the approval evaluator consults to turn scores into a decision.

Pure domain: standard library, the shared-kernel error base, the profile model, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.policy.profile import ReviewProfile
from creative_director.domain.shared.value_objects import ReviewMode, Score

__all__ = ["InvalidPolicyError", "ReviewPolicy"]


class InvalidPolicyError(DesignDirectorError):
    """Raised when a review policy is constructed with invalid data."""

    code = "invalid_creative_director_policy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ReviewPolicy:
    """The profile, mode, and threshold a review is judged by.

    Attributes:
        profile: The calibrated profile (weights + hard gates + default threshold).
        mode: How the final decision is arrived at.
        threshold_override: An optional overall threshold for this run only.
    """

    profile: ReviewProfile
    mode: ReviewMode = ReviewMode.AUTOMATIC
    threshold_override: Score | None = None

    @property
    def effective_threshold(self) -> Score:
        """The overall threshold in force (override if set, else the profile default)."""
        return self.threshold_override or self.profile.default_threshold
