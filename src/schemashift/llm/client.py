"""LLM client factory and interface.

Spec: llm-assist/client
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from schemashift.config import LLMConfig
from schemashift.errors import ConfigurationError
from schemashift.llm.cache import LLMCache
from schemashift.llm.providers import BaseProvider, NoneProvider, OpenAIProvider, ReplayProvider

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Unified client wrapping underlying LLM providers."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def complete(self, prompt: str, schema: type[T]) -> T | None:
        """Query LLM and parse into Pydantic model *schema*, or return None."""
        return self._provider.complete(prompt, schema)


def get_llm_client(config: LLMConfig) -> LLMClient:
    """Factory to create configured LLM client."""
    cache = LLMCache(config.cache_dir)
    provider_name = config.provider.lower().strip()

    if provider_name == "none":
        return LLMClient(NoneProvider())
    elif provider_name == "replay":
        return LLMClient(ReplayProvider(cache, config.model))
    elif provider_name == "openai":
        return LLMClient(OpenAIProvider(config, cache))
    else:
        raise ConfigurationError(
            f"Unknown LLM provider '{config.provider}'.",
            hint="Choose one of: none, replay, openai.",
        )
