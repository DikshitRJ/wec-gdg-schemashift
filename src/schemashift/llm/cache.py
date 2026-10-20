"""Record and replay store for LLM responses.

Spec: llm-assist/cache
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class LLMCache:
    """File-based cache for LLM responses keyed by sha256(provider|model|prompt)."""

    def __init__(self, cache_dir: str | Path = "workspace/llm_cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, provider: str, model: str, prompt: str) -> str:
        content = f"{provider}|{model}|{prompt}".encode()
        return hashlib.sha256(content).hexdigest()

    def get(self, provider: str, model: str, prompt: str) -> str | None:
        """Retrieve cached text or return None."""
        key = self._key(provider, model, prompt)
        entry_file = self.cache_dir / f"{key}.json"
        if entry_file.exists():
            try:
                data = json.loads(entry_file.read_text(encoding="utf-8"))
                resp = data.get("response")
                return str(resp) if resp is not None else None
            except Exception:
                return None
        return None

    def put(self, provider: str, model: str, prompt: str, response: str) -> None:
        """Store response in cache."""
        key = self._key(provider, model, prompt)
        entry_file = self.cache_dir / f"{key}.json"
        data = {
            "key": key,
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "response": response,
        }
        entry_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
