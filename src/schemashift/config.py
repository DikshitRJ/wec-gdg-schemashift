"""Configuration: YAML + environment interpolation → typed Settings.

Spec: foundation/config
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


def _interpolate_env(value: Any) -> Any:
    """Recursively interpolate ${VAR} and ${VAR:-default} in strings."""
    if isinstance(value, str):
        def _replace(m: re.Match) -> str:
            var = m.group(1)
            if ":-" in var:
                name, default = var.split(":-", 1)
                return os.environ.get(name, default)
            return os.environ.get(var, m.group(0))
        return re.sub(r"\$\{([^}]+)\}", _replace, value)
    if isinstance(value, dict):
        return {k: _interpolate_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env(v) for v in value]
    return value


class SourceConfig(BaseModel):
    uri: str = "mongodb://localhost:27017"
    database: str = "shop"


class TargetConfig(BaseModel):
    uri: str = "postgresql://schemashift:schemashift@localhost:5432/schemashift"
    schema_name: str = Field(default="public", alias="schema")
    reset_target: bool = True


class SamplingConfig(BaseModel):
    size: int = 1000


class InferenceConfig(BaseModel):
    embed_max_fields: int = 8
    ref_hit_rate: float = 0.98
    jsonb_variance_threshold: float = 0.4
    array_scalar_strategy: str = "table"  # table | pg_array


class ScoringWeights(BaseModel):
    name: float = 0.35
    type: float = 0.35
    structure: float = 0.20
    constraints: float = 0.10


class ScoringConfig(BaseModel):
    weights: ScoringWeights = ScoringWeights()
    matched: float = 0.85
    guessed: float = 0.60


class MigrationConfig(BaseModel):
    batch_size: int = 500
    all_or_nothing: bool = True
    max_remap_attempts: int = 2
    retries: int = 3


class LLMConfig(BaseModel):
    provider: str = "none"  # none | replay | openai
    model: str = "gemini-2.5-flash"
    api_base: str = ""
    api_key: str = ""
    cache_dir: str = "workspace/llm_cache"
    redact: bool = True


class PathsConfig(BaseModel):
    out: str = "workspace/out"


class Settings(BaseModel):
    """Top-level configuration for SchemaShift."""

    source: SourceConfig = SourceConfig()
    target: TargetConfig = TargetConfig()
    sampling: SamplingConfig = SamplingConfig()
    inference: InferenceConfig = InferenceConfig()
    scoring: ScoringConfig = ScoringConfig()
    migration: MigrationConfig = MigrationConfig()
    llm: LLMConfig = LLMConfig()
    overrides_file: str = "workspace/out/state/overrides.yaml"
    paths: PathsConfig = PathsConfig()

    @classmethod
    def load(cls, config_path: str | Path = "workspace/schemashift.yaml") -> "Settings":
        """Load settings from YAML with environment interpolation."""
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                raw = yaml.safe_load(f) or {}
            data = _interpolate_env(raw)
        else:
            data = {}

        # Also read env vars for LLM config
        if "llm" not in data:
            data["llm"] = {}
        llm = data["llm"]
        if not llm.get("api_base"):
            llm["api_base"] = os.environ.get("SCHEMASHIFT_LLM_API_BASE", "")
        if not llm.get("api_key"):
            llm["api_key"] = os.environ.get("SCHEMASHIFT_LLM_API_KEY", "")

        # Source/target from env
        if "source" not in data:
            data["source"] = {}
        if not data["source"].get("uri"):
            data["source"]["uri"] = os.environ.get(
                "MONGO_URI", "mongodb://localhost:27017"
            )
        if "target" not in data:
            data["target"] = {}
        if not data["target"].get("uri"):
            data["target"]["uri"] = os.environ.get(
                "PG_URI",
                "postgresql://schemashift:schemashift@localhost:5432/schemashift",
            )

        return cls.model_validate(data)
