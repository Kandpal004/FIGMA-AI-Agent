"""LLM client abstraction.

A single, provider-agnostic entry point (:class:`LLMClient`) that agents use for
all model calls. Centralizing it here gives us one place for retries, timeouts,
token accounting, and model routing (Opus for reasoning, Haiku for mechanical
work) — instead of each of the 20 agents re-implementing that logic.
"""

from core.llm.client import LLMClient, LLMResponse

__all__ = ["LLMClient", "LLMResponse"]
