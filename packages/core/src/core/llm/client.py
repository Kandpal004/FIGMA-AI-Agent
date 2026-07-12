"""Anthropic Claude client with retries, timeouts, and token accounting.

This is the concrete implementation behind the :class:`~core.contracts.agent.LLMPort`
protocol. Agents receive it via their :class:`~core.contracts.agent.AgentContext`
and call :meth:`LLMClient.complete`.

Responsibilities kept here (so no agent re-implements them):

* **Model routing** — a symbolic tier (``"default"`` / ``"fast"``) resolves to
  a concrete model id from settings, so we can retune the whole fleet centrally.
* **Retries with exponential backoff** on transient errors (rate limits,
  timeouts, 5xx), bounded by ``LLM_MAX_RETRIES``.
* **Uniform error mapping** onto :mod:`core.errors`.
* **Token accounting** returned on every response for cost observability.

The Anthropic SDK import is done lazily inside the constructor so that `core`
can be imported (and its contracts used in tests) without the SDK installed.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.config import Settings, get_settings
from core.errors import LLMError, LLMRateLimitError, LLMTimeoutError
from core.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field

log = get_logger(__name__)


class LLMResponse(BaseModel):
    """Normalized result of a completion call."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Concatenated text content of the reply.")
    model: str = Field(description="The concrete model id that served the request.")
    tokens_input: int = Field(default=0, ge=0)
    tokens_output: int = Field(default=0, ge=0)
    stop_reason: str | None = None


class LLMClient:
    """Async wrapper around the Anthropic Messages API.

    Satisfies :class:`~core.contracts.agent.LLMPort`. Construct once per process
    and share; the underlying HTTP client is connection-pooled and thread-safe.
    """

    #: Symbolic tiers agents can request without knowing concrete model ids.
    _TIER_DEFAULT = "default"
    _TIER_FAST = "fast"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        # Lazy import keeps the SDK optional for contract-only consumers/tests.
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover - exercised only w/o SDK
            raise LLMError(
                "The 'anthropic' package is required to use LLMClient.",
                details={"hint": "uv add anthropic"},
            ) from exc

        self._client = AsyncAnthropic(
            api_key=self._settings.anthropic_api_key.get_secret_value(),
            timeout=self._settings.llm_timeout_seconds,
            max_retries=0,  # We own retry policy explicitly (see _with_retries).
        )

    # ------------------------------------------------------------------ #
    def _resolve_model(self, model: str | None) -> str:
        """Map a symbolic tier or explicit id to a concrete model id."""
        if model in (None, self._TIER_DEFAULT):
            return self._settings.llm_default_model
        if model == self._TIER_FAST:
            return self._settings.llm_fast_model
        return model

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Run a single completion.

        Args:
            system: The system prompt establishing the agent's role.
            messages: Anthropic-format message list (``[{"role", "content"}]``).
            model: ``"default"``, ``"fast"``, an explicit model id, or None
                (treated as default).
            max_tokens: Output cap; defaults to ``LLM_MAX_OUTPUT_TOKENS``.

        Returns:
            A normalized :class:`LLMResponse`.

        Raises:
            LLMRateLimitError, LLMTimeoutError, LLMError: on exhausted retries.
        """
        resolved_model = self._resolve_model(model)
        cap = max_tokens or self._settings.llm_max_output_tokens

        async def _call() -> LLMResponse:
            response = await self._client.messages.create(
                model=resolved_model,
                system=system,
                messages=messages,
                max_tokens=cap,
            )
            text = "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            )
            return LLMResponse(
                text=text,
                model=resolved_model,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
                stop_reason=response.stop_reason,
            )

        return await self._with_retries(_call, model=resolved_model)

    # ------------------------------------------------------------------ #
    async def _with_retries(self, call: Any, *, model: str) -> LLMResponse:
        """Execute `call`, retrying transient failures with exponential backoff."""
        from anthropic import (
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )

        max_retries = self._settings.llm_max_retries
        attempt = 0
        while True:
            try:
                return await call()
            except RateLimitError as exc:
                mapped: LLMError = LLMRateLimitError(
                    "LLM provider rate-limited the request.", details={"model": model}
                )
                retryable = True
                original: Exception = exc
            except (APITimeoutError, asyncio.TimeoutError) as exc:
                mapped = LLMTimeoutError("LLM request timed out.", details={"model": model})
                retryable = True
                original = exc
            except (APIConnectionError, InternalServerError) as exc:
                mapped = LLMError(
                    "Transient LLM provider error.",
                    code="llm_transient",
                    details={"model": model},
                )
                retryable = True
                original = exc
            except Exception as exc:  # noqa: BLE001 - map anything else to a hard error
                raise LLMError(
                    f"LLM request failed: {exc}", details={"model": model}
                ) from exc

            if not retryable or attempt >= max_retries:
                raise mapped from original

            backoff = min(2**attempt, 30)
            log.warning(
                "llm call failed, retrying",
                extra={"attempt": attempt + 1, "backoff_s": backoff, "model": model},
            )
            await asyncio.sleep(backoff)
            attempt += 1
