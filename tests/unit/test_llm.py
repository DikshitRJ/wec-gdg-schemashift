"""Unit tests for LLM client, cache, guard, and providers.

Spec: llm-assist/unit-test
"""

import pytest
from pydantic import BaseModel

from schemashift.config import LLMConfig
from schemashift.errors import LLMCacheMiss
from schemashift.llm.cache import LLMCache
from schemashift.llm.client import get_llm_client
from schemashift.llm.guard import parse_and_validate, redact_prompt


class SampleOutput(BaseModel):
    message: str
    count: int


def test_redact_prompt():
    prompt = "Connecting to mongodb://user:secret@localhost:27017 and password='hidden'"
    redacted = redact_prompt(prompt)
    assert "secret" not in redacted
    assert "hidden" not in redacted
    assert "redacted" in redacted


def test_parse_and_validate():
    valid_json = '{"message": "hello", "count": 42}'
    res = parse_and_validate(valid_json, SampleOutput)
    assert res is not None
    assert res.message == "hello"
    assert res.count == 42

    codeblock = '```json\n{"message": "wrapped", "count": 1}\n```'
    res2 = parse_and_validate(codeblock, SampleOutput)
    assert res2 is not None
    assert res2.message == "wrapped"

    invalid_json = "not json at all"
    assert parse_and_validate(invalid_json, SampleOutput) is None


def test_none_provider():
    cfg = LLMConfig(provider="none")
    client = get_llm_client(cfg)
    assert client.complete("test prompt", SampleOutput) is None


def test_replay_provider(tmp_path):
    cache = LLMCache(tmp_path)
    prompt = "Suggest something"
    cache.put("openai", "gemini-2.5-flash", prompt, '{"message": "cached", "count": 7}')

    cfg = LLMConfig(provider="replay", model="gemini-2.5-flash", cache_dir=str(tmp_path))
    client = get_llm_client(cfg)
    res = client.complete(prompt, SampleOutput)
    assert res is not None
    assert res.message == "cached"

    with pytest.raises(LLMCacheMiss):
        client.complete("unseen prompt", SampleOutput)
