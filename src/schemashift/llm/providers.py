"""LLM provider implementations: none, replay, and openai-compatible.

Spec: llm-assist/providers
"""

from __future__ import annotations

from typing import Type, TypeVar
from pydantic import BaseModel

from schemashift.config import LLMConfig
from schemashift.errors import ConfigurationError, LLMCacheMiss
from schemashift.llm.cache import LLMCache
from schemashift.llm.guard import parse_and_validate, redact_prompt

T = TypeVar("T", bound=BaseModel)


class BaseProvider:
    """Base class for LLM providers."""

    def complete(self, prompt: str, schema: Type[T]) -> T | None:
        raise NotImplementedError


class NoneProvider(BaseProvider):
    """Null provider that always returns None, triggering deterministic fallbacks."""

    def complete(self, prompt: str, schema: Type[T]) -> T | None:
        return None


class ReplayProvider(BaseProvider):
    """Replay provider that serves exclusively from local cache."""

    def __init__(self, cache: LLMCache, model: str) -> None:
        self.cache = cache
        self.model = model

    def complete(self, prompt: str, schema: Type[T]) -> T | None:
        clean_prompt = redact_prompt(prompt)
        cached = self.cache.get("openai", self.model, clean_prompt)
        if cached is None:
            # Also try 'replay' as provider name
            cached = self.cache.get("replay", self.model, clean_prompt)

        if cached is None:
            raise LLMCacheMiss(
                f"Cache miss in replay provider for prompt hash.",
                hint="Run once with provider=openai or add response to workspace/llm_cache.",
            )
        return parse_and_validate(cached, schema)


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI-compatible APIs (including Google Gemini via OpenAI endpoint)."""

    def __init__(self, config: LLMConfig, cache: LLMCache) -> None:
        self.config = config
        self.cache = cache

        if not config.api_key:
            raise ConfigurationError(
                "LLM api_key is missing. Set SCHEMASHIFT_LLM_API_KEY environment variable.",
                hint="Export SCHEMASHIFT_LLM_API_KEY or use provider=none.",
            )

        try:
            import openai
        except ImportError as exc:
            raise ConfigurationError(
                "openai package is not installed.",
                hint="Install with `uv add openai`.",
            ) from exc

        client_kwargs = {"api_key": config.api_key}
        if config.api_base:
            client_kwargs["base_url"] = config.api_base

        self.client = openai.OpenAI(**client_kwargs)

    def complete(self, prompt: str, schema: Type[T]) -> T | None:
        clean_prompt = redact_prompt(prompt) if self.config.redact else prompt

        # Check cache first
        cached = self.cache.get("openai", self.config.model, clean_prompt)
        if cached is not None:
            res = parse_and_validate(cached, schema)
            if res is not None:
                return res

        # Generate via API
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a database migration assistant. Respond ONLY with valid JSON conforming to the requested schema. Do not include markdown codeblocks or explanations outside the JSON.",
                    },
                    {"role": "user", "content": clean_prompt},
                ],
                temperature=0.0,
            )
            raw_text = response.choices[0].message.content or ""
            # Save to cache
            self.cache.put("openai", self.config.model, clean_prompt, raw_text)
            return parse_and_validate(raw_text, schema)
        except Exception as exc:
            # Fall back to None on API error
            return None
